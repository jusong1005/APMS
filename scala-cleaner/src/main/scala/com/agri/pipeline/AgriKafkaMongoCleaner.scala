package com.agri.pipeline

import org.apache.spark.sql.{Column, DataFrame, SparkSession}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.streaming.{DataStreamWriter, StreamingQuery, Trigger}
import org.apache.spark.sql.types._

object AgriKafkaMongoCleaner {
  private val DefaultBootstrapServers = "127.0.0.1:9092"
  private val DefaultRawPriceTopic = "raw_price_topic"
  private val DefaultRawWeatherTopic = "raw_weather_topic"
  private val DefaultMongoUri = "mongodb://127.0.0.1:27017"
  private val DefaultMongoDatabase = "agri_price"
  private val DefaultCheckpointDir = "file:///data/spark/checkpoints/agri-cleaner"

  final case class Options(
      bootstrapServers: String = envOrDefault("KAFKA_BOOTSTRAP_SERVERS", DefaultBootstrapServers),
      rawPriceTopic: String = envOrDefault("KAFKA_RAW_PRICE_TOPIC", DefaultRawPriceTopic),
      rawWeatherTopic: String = envOrDefault("KAFKA_RAW_WEATHER_TOPIC", DefaultRawWeatherTopic),
      mongoUri: String = envOrDefault("MONGODB_URI", DefaultMongoUri),
      mongoDatabase: String = envOrDefault("MONGODB_DATABASE", DefaultMongoDatabase),
      checkpointDir: String = envOrDefault("SCALA_CLEANER_CHECKPOINT_DIR", DefaultCheckpointDir),
      once: Boolean = false
  )

  private val payloadSchema = StructType(
    Seq(
      StructField("product_name", StringType),
      StructField("product_category", StringType),
      StructField("market_name", StringType),
      StructField("region", StringType),
      StructField("date", StringType),
      StructField("collect_time", StringType),
      StructField("highest_price", StringType),
      StructField("lowest_price", StringType),
      StructField("average_price", StringType),
      StructField("price", StringType),
      StructField("unit", StringType),
      StructField("source_url", StringType),
      StructField("weather_condition", StringType),
      StructField("average_temperature", StringType),
      StructField("highest_temperature", StringType),
      StructField("lowest_temperature", StringType),
      StructField("rainfall", StringType),
      StructField("humidity", StringType),
      StructField("sunshine_duration", StringType)
    )
  )

  private val envelopeSchema = StructType(
    Seq(
      StructField("event_id", StringType),
      StructField("event_type", StringType),
      StructField("collected_at", StringType),
      StructField("payload", payloadSchema)
    )
  )

  def main(args: Array[String]): Unit = {
    val options = parseArgs(args.toList)
    val spark = SparkSession
      .builder()
      .appName("AgriKafkaMongoScalaCleaner")
      .config("spark.mongodb.write.connection.uri", options.mongoUri)
      .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    val rawEvents = readKafkaEvents(spark, options)
    val parsedEvents = parseEvents(rawEvents, options)

    val priceWithStatus = cleanPriceEvents(parsedEvents, options.rawPriceTopic)
    val weatherWithStatus = cleanWeatherEvents(parsedEvents, options.rawWeatherTopic)

    val validPrice = priceWithStatus.filter(col("validation_error").isNull).drop("validation_error", "raw_json")
    val validWeather = weatherWithStatus.filter(col("validation_error").isNull).drop("validation_error", "raw_json")
    val invalidEvents = priceWithStatus
      .filter(col("validation_error").isNotNull)
      .selectInvalid("price")
      .unionByName(weatherWithStatus.filter(col("validation_error").isNotNull).selectInvalid("weather"))

    val trigger = if (options.once) Trigger.AvailableNow() else Trigger.ProcessingTime("30 seconds")
    val queries = Seq(
      writeMongoStream(validPrice, options, "price_data", s"${options.checkpointDir}/price", trigger),
      writeMongoStream(validWeather, options, "weather_data", s"${options.checkpointDir}/weather", trigger),
      writeMongoStream(invalidEvents, options, "invalid_events", s"${options.checkpointDir}/invalid", trigger)
    )

    if (options.once) {
      queries.foreach(_.awaitTermination())
    } else {
      spark.streams.awaitAnyTermination()
    }
  }

  private def readKafkaEvents(spark: SparkSession, options: Options): DataFrame = {
    spark.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", options.bootstrapServers)
      .option("subscribe", Seq(options.rawPriceTopic, options.rawWeatherTopic).mkString(","))
      .option("startingOffsets", "earliest")
      .option("failOnDataLoss", "false")
      .load()
      .select(
        col("topic").as("source_topic"),
        col("timestamp").as("kafka_timestamp"),
        col("key").cast("string").as("message_key"),
        col("value").cast("string").as("raw_json")
      )
  }

  private def parseEvents(rawEvents: DataFrame, options: Options): DataFrame = {
    rawEvents
      .withColumn("event", from_json(col("raw_json"), envelopeSchema))
      .withColumn("direct_payload", from_json(col("raw_json"), payloadSchema))
      .withColumn(
        "event_type",
        coalesce(
          col("event.event_type"),
          when(col("source_topic") === lit(options.rawPriceTopic), lit("price"))
            .when(col("source_topic") === lit(options.rawWeatherTopic), lit("weather"))
        )
      )
      .withColumn("source_event_id", col("event.event_id"))
  }

  private def cleanPriceEvents(events: DataFrame, rawPriceTopic: String): DataFrame = {
    val priceDate = normalizeDate(coalesce(payloadCol("date"), payloadCol("collect_time")))
    val averagePrice = normalizeNumber(coalesce(payloadCol("average_price"), payloadCol("price")))
    val highPrice = coalesce(normalizeNumber(payloadCol("highest_price")), averagePrice)
    val lowPrice = coalesce(normalizeNumber(payloadCol("lowest_price")), averagePrice)

    events
      .filter(col("event_type") === lit("price") || col("source_topic") === lit(rawPriceTopic))
      .select(
        deterministicId(
          cleanText(payloadCol("product_name"), ""),
          cleanText(payloadCol("market_name"), ""),
          cleanText(payloadCol("region"), "其他"),
          priceDate,
          cleanText(payloadCol("unit"), "元/公斤")
        ).as("_id"),
        cleanText(payloadCol("product_name"), "").as("product_name"),
        cleanText(payloadCol("product_category"), "其他").as("product_category"),
        cleanText(payloadCol("market_name"), "").as("market_name"),
        cleanText(payloadCol("region"), "其他").as("region"),
        priceDate.as("date"),
        when(lowPrice > highPrice, highPrice).otherwise(lowPrice).as("lowest_price"),
        when(lowPrice > highPrice, lowPrice).otherwise(highPrice).as("highest_price"),
        averagePrice.as("average_price"),
        cleanText(payloadCol("unit"), "元/公斤").as("unit"),
        cleanText(payloadCol("source_url"), null).as("source_url"),
        col("source_event_id"),
        col("source_topic"),
        col("raw_json"),
        current_timestamp().as("ingested_at")
      )
      .withColumn(
        "validation_error",
        when(col("product_name") === "", lit("missing product_name"))
          .when(col("market_name") === "", lit("missing market_name"))
          .when(col("date").isNull, lit("invalid date"))
          .when(col("average_price").isNull || col("average_price") <= 0, lit("invalid average_price"))
      )
      .dropDuplicates("_id")
  }

  private def cleanWeatherEvents(events: DataFrame, rawWeatherTopic: String): DataFrame = {
    val weatherDate = normalizeDate(payloadCol("date"))
    events
      .filter(col("event_type") === lit("weather") || col("source_topic") === lit(rawWeatherTopic))
      .select(
        deterministicId(cleanText(payloadCol("region"), ""), weatherDate).as("_id"),
        cleanText(payloadCol("region"), "").as("region"),
        weatherDate.as("date"),
        normalizeNumber(payloadCol("average_temperature")).as("average_temperature"),
        normalizeNumber(payloadCol("highest_temperature")).as("highest_temperature"),
        normalizeNumber(payloadCol("lowest_temperature")).as("lowest_temperature"),
        normalizeNumber(payloadCol("rainfall")).as("rainfall"),
        normalizeNumber(payloadCol("humidity")).as("humidity"),
        normalizeNumber(payloadCol("sunshine_duration")).as("sunshine_duration"),
        cleanText(payloadCol("weather_condition"), "未知").as("weather_condition"),
        col("source_event_id"),
        col("source_topic"),
        col("raw_json"),
        current_timestamp().as("ingested_at")
      )
      .withColumn(
        "validation_error",
        when(col("region") === "", lit("missing region"))
          .when(col("date").isNull, lit("invalid date"))
      )
      .dropDuplicates("_id")
  }

  private def writeMongoStream(
      streamDf: DataFrame,
      options: Options,
      collection: String,
      checkpointLocation: String,
      trigger: Trigger
  ): StreamingQuery = {
    streamDf.writeStream
      .outputMode("append")
      .option("checkpointLocation", checkpointLocation)
      .trigger(trigger)
      .foreachBatch { (batchDf: DataFrame, _: Long) =>
        if (!batchDf.isEmpty) {
          batchDf.write
            .format("mongodb")
            .mode("append")
            .option("database", options.mongoDatabase)
            .option("collection", collection)
            .save()
        }
      }
      .start()
  }

  private def payloadCol(field: String): Column = {
    coalesce(col(s"event.payload.$field"), col(s"direct_payload.$field"))
  }

  private def cleanText(value: Column, defaultValue: String): Column = {
    val cleaned = trim(coalesce(value.cast(StringType), lit("")))
    val defaultColumn = if (defaultValue == null) lit(null).cast(StringType) else lit(defaultValue)
    when(length(cleaned) > 0, cleaned).otherwise(defaultColumn)
  }

  private def normalizeDate(value: Column): Column = {
    val normalizedText = regexp_replace(trim(coalesce(value.cast(StringType), lit(""))), "/", "-")
    to_date(normalizedText)
  }

  private def normalizeNumber(value: Column): Column = {
    val numericText = regexp_replace(trim(coalesce(value.cast(StringType), lit(""))), "[^0-9.\\-]", "")
    bround(when(length(numericText) > 0, numericText.cast(DoubleType)), 2)
  }

  private def deterministicId(parts: Column*): Column = {
    sha2(concat_ws("|", parts.map(part => coalesce(part.cast(StringType), lit(""))): _*), 256)
  }

  private def parseArgs(args: List[String], current: Options = Options()): Options = {
    args match {
      case Nil => current
      case "--bootstrap-servers" :: value :: tail => parseArgs(tail, current.copy(bootstrapServers = value))
      case "--raw-price-topic" :: value :: tail => parseArgs(tail, current.copy(rawPriceTopic = value))
      case "--raw-weather-topic" :: value :: tail => parseArgs(tail, current.copy(rawWeatherTopic = value))
      case "--mongodb-uri" :: value :: tail => parseArgs(tail, current.copy(mongoUri = value))
      case "--mongodb-database" :: value :: tail => parseArgs(tail, current.copy(mongoDatabase = value))
      case "--checkpoint-dir" :: value :: tail => parseArgs(tail, current.copy(checkpointDir = value))
      case "--once" :: tail => parseArgs(tail, current.copy(once = true))
      case "--help" :: _ =>
        printUsage()
        sys.exit(0)
      case unknown :: _ =>
        System.err.println(s"Unknown argument: $unknown")
        printUsage()
        sys.exit(1)
    }
  }

  private def printUsage(): Unit = {
    println(
      """Usage: spark-submit --class com.agri.pipeline.AgriKafkaMongoCleaner <jar> [options]
        |
        |Options:
        |  --bootstrap-servers <host:port>  Kafka bootstrap servers, default 127.0.0.1:9092
        |  --raw-price-topic <topic>        Raw price topic, default raw_price_topic
        |  --raw-weather-topic <topic>      Raw weather topic, default raw_weather_topic
        |  --mongodb-uri <uri>              MongoDB URI, default mongodb://127.0.0.1:27017
        |  --mongodb-database <name>        MongoDB database, default agri_price
        |  --checkpoint-dir <path>          Spark checkpoint directory
        |  --once                           Process available records and exit
        |""".stripMargin
    )
  }

  private def envOrDefault(name: String, defaultValue: String): String = {
    Option(System.getenv(name)).filter(_.trim.nonEmpty).getOrElse(defaultValue)
  }

  implicit final class InvalidSelectionOps(private val df: DataFrame) extends AnyVal {
    def selectInvalid(eventType: String): DataFrame = {
      df.select(
        deterministicId(lit(eventType), col("raw_json")).as("_id"),
        lit(eventType).as("event_type"),
        col("source_event_id"),
        col("source_topic"),
        col("validation_error"),
        col("raw_json"),
        current_timestamp().as("ingested_at")
      )
    }
  }
}