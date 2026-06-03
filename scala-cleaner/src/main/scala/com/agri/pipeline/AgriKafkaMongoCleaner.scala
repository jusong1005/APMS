package com.agri.pipeline

import java.time.Instant
import java.util.Locale

import org.apache.spark.sql.{Column, DataFrame, SparkSession}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.streaming.{DataStreamWriter, StreamingQuery, Trigger}
import org.apache.spark.sql.types._
import redis.clients.jedis.Jedis

object AgriKafkaMongoCleaner {
  private val DefaultBootstrapServers = "127.0.0.1:9092"
  private val DefaultRawPriceTopic = "raw_price_topic"
  private val DefaultRawWeatherTopic = "raw_weather_topic"
  private val DefaultMongoUri = "mongodb://127.0.0.1:27017"
  private val DefaultMongoDatabase = "agri_price"
  private val DefaultCheckpointDir = "file:///data/spark/checkpoints/agri-cleaner"
  private val DefaultProcessingInterval = "10 minutes"
  private val DefaultRedisHost = "127.0.0.1"
  private val DefaultRedisPort = 6379
  private val DefaultRedisDatabase = 0
  private val DefaultRedisKeyPrefix = "agri:realtime"
  private val DefaultRedisAlertThresholdPercent = 20.0
  private val DefaultRedisLatestRecordLimit = 200

  final case class Options(
      bootstrapServers: String = envOrDefault("KAFKA_BOOTSTRAP_SERVERS", DefaultBootstrapServers),
      rawPriceTopic: String = envOrDefault("KAFKA_RAW_PRICE_TOPIC", DefaultRawPriceTopic),
      rawWeatherTopic: String = envOrDefault("KAFKA_RAW_WEATHER_TOPIC", DefaultRawWeatherTopic),
      mongoUri: String = envOrDefault("MONGODB_URI", DefaultMongoUri),
      mongoDatabase: String = envOrDefault("MONGODB_DATABASE", DefaultMongoDatabase),
      checkpointDir: String = envOrDefault("SCALA_CLEANER_CHECKPOINT_DIR", DefaultCheckpointDir),
    processingInterval: String = envOrDefault("SCALA_CLEANER_PROCESSING_INTERVAL", DefaultProcessingInterval),
    redisHost: String = envOrDefault("REDIS_HOST", DefaultRedisHost),
    redisPort: Int = envOrDefault("REDIS_PORT", DefaultRedisPort.toString).toInt,
    redisDatabase: Int = envOrDefault("REDIS_DATABASE", DefaultRedisDatabase.toString).toInt,
    redisKeyPrefix: String = envOrDefault("REDIS_KEY_PREFIX", DefaultRedisKeyPrefix),
    redisAlertThresholdPercent: Double = envOrDefault("REDIS_ALERT_THRESHOLD_PERCENT", DefaultRedisAlertThresholdPercent.toString).toDouble,
    redisLatestRecordLimit: Int = envOrDefault("REDIS_LATEST_RECORD_LIMIT", DefaultRedisLatestRecordLimit.toString).toInt,
      once: Boolean = false
  )

  final case class ProductRegionStat(
    productName: String,
    region: String,
    recordCount: Long,
    averagePrice: Double,
    minPrice: Double,
    maxPrice: Double
  )

  final case class PriceAlert(
    productName: String,
    region: String,
    previousAveragePrice: Double,
    currentAveragePrice: Double,
    changeRatePercent: Double,
    alertLevel: String,
    batchId: Long,
    detectedAt: String
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

    val trigger = if (options.once) Trigger.AvailableNow() else Trigger.ProcessingTime(options.processingInterval)
    val queries = Seq(
      writePriceStream(validPrice, options, trigger),
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

  private def writePriceStream(streamDf: DataFrame, options: Options, trigger: Trigger): StreamingQuery = {
    streamDf.writeStream
      .outputMode("append")
      .option("checkpointLocation", s"${options.checkpointDir}/price")
      .trigger(trigger)
      .foreachBatch { (batchDf: DataFrame, batchId: Long) =>
        val cachedBatch = batchDf.persist()
        try {
          val batchCount = cachedBatch.count()
          if (batchCount > 0) {
            cachedBatch.write
              .format("mongodb")
              .mode("append")
              .option("database", options.mongoDatabase)
              .option("collection", "price_data")
              .save()
          }
          writeRealtimePriceRedis(cachedBatch, options, batchId, batchCount)
        } finally {
          cachedBatch.unpersist()
        }
      }
      .start()
  }

  private def writeRealtimePriceRedis(
      batchDf: DataFrame,
      options: Options,
      batchId: Long,
      batchCount: Long
  ): Unit = {
    val detectedAt = Instant.now().toString
    val averagePrice = if (batchCount > 0) readAveragePrice(batchDf) else None
    val productRegionStats = if (batchCount > 0) collectProductRegionStats(batchDf) else Array.empty[ProductRegionStat]
    val latestRecordsJson = if (batchCount > 0) collectLatestRecordsJson(batchDf, options.redisLatestRecordLimit) else "[]"

    val jedis = new Jedis(options.redisHost, options.redisPort)
    try {
      jedis.select(options.redisDatabase)
      val prefix = options.redisKeyPrefix.stripSuffix(":")
      val baselineKey = s"$prefix:baseline:product_region_avg_price"
      val productRegionStatsKey = s"$prefix:product_region_stats"

      val alerts = detectAlerts(jedis, baselineKey, productRegionStats, options, batchId, detectedAt)
      productRegionStats.foreach { stat =>
        val field = productRegionField(stat.productName, stat.region)
        jedis.hset(baselineKey, field, formatDouble(stat.averagePrice))
        jedis.hset(productRegionStatsKey, field, productRegionStatJson(stat))
      }

      val summaryJson = jsonObject(
        Seq(
          "batch_id" -> batchId.toString,
          "processed_at" -> jsonString(detectedAt),
          "batch_count" -> batchCount.toString,
          "realtime_average_price" -> jsonNullableDouble(averagePrice),
          "product_region_group_count" -> productRegionStats.length.toString,
          "alert_threshold_percent" -> formatDouble(options.redisAlertThresholdPercent),
          "alert_count" -> alerts.length.toString,
          "status" -> jsonString(if (alerts.nonEmpty) "warning" else "normal")
        )
      )
      val alertsJson = alerts.map(priceAlertJson).mkString("[", ",", "]")

      jedis.set(s"$prefix:last_batch", summaryJson)
      jedis.set(s"$prefix:latest_prices", latestRecordsJson)
      jedis.set(s"$prefix:latest_alerts", alertsJson)
      jedis.hset(s"$prefix:metrics", "latest_batch_count", batchCount.toString)
      jedis.hset(s"$prefix:metrics", "realtime_average_price", jsonNullableDouble(averagePrice).replace("\"", ""))
      jedis.hset(s"$prefix:metrics", "alert_count", alerts.length.toString)
      jedis.hset(s"$prefix:metrics", "last_processed_at", detectedAt)
    } catch {
      case error: Exception => System.err.println(s"Failed to write realtime price metrics to Redis: ${error.getMessage}")
    } finally {
      jedis.close()
    }
  }

  private def readAveragePrice(batchDf: DataFrame): Option[Double] = {
    val row = batchDf.agg(round(avg(col("average_price")), 2).as("realtime_average_price")).first()
    Option(row.getAs[java.lang.Double]("realtime_average_price")).map(_.doubleValue())
  }

  private def collectProductRegionStats(batchDf: DataFrame): Array[ProductRegionStat] = {
    batchDf
      .groupBy(col("product_name"), col("region"))
      .agg(
        count(lit(1)).as("record_count"),
        round(avg(col("average_price")), 2).as("average_price"),
        round(min(col("average_price")), 2).as("min_price"),
        round(max(col("average_price")), 2).as("max_price")
      )
      .collect()
      .flatMap { row =>
        val averagePrice = Option(row.getAs[java.lang.Double]("average_price")).map(_.doubleValue())
        val minPrice = Option(row.getAs[java.lang.Double]("min_price")).map(_.doubleValue())
        val maxPrice = Option(row.getAs[java.lang.Double]("max_price")).map(_.doubleValue())
        averagePrice.map { value =>
          ProductRegionStat(
            row.getAs[String]("product_name"),
            row.getAs[String]("region"),
            row.getAs[Long]("record_count"),
            value,
            minPrice.getOrElse(value),
            maxPrice.getOrElse(value)
          )
        }
      }
  }

  private def collectLatestRecordsJson(batchDf: DataFrame, limit: Int): String = {
    batchDf
      .select(
        col("product_name"),
        col("product_category"),
        col("market_name"),
        col("region"),
        col("date").cast(StringType).as("date"),
        col("average_price"),
        col("lowest_price"),
        col("highest_price"),
        col("unit"),
        col("ingested_at").cast(StringType).as("ingested_at")
      )
      .orderBy(col("ingested_at").desc_nulls_last)
      .limit(limit)
      .toJSON
      .collect()
      .mkString("[", ",", "]")
  }

  private def detectAlerts(
      jedis: Jedis,
      baselineKey: String,
      currentStats: Array[ProductRegionStat],
      options: Options,
      batchId: Long,
      detectedAt: String
  ): Array[PriceAlert] = {
    currentStats.flatMap { stat =>
      val previousValue = Option(jedis.hget(baselineKey, productRegionField(stat.productName, stat.region))).flatMap(toDoubleOption)
      previousValue.flatMap { previousAverage =>
        if (previousAverage > 0) {
          val changeRate = (stat.averagePrice - previousAverage) / previousAverage * 100
          val roundedRate = roundDouble(changeRate)
          if (math.abs(roundedRate) >= options.redisAlertThresholdPercent) {
            Some(
              PriceAlert(
                stat.productName,
                stat.region,
                roundDouble(previousAverage),
                roundDouble(stat.averagePrice),
                roundedRate,
                if (math.abs(roundedRate) >= options.redisAlertThresholdPercent * 2) "high" else "medium",
                batchId,
                detectedAt
              )
            )
          } else {
            None
          }
        } else {
          None
        }
      }
    }
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
      case "--processing-interval" :: value :: tail => parseArgs(tail, current.copy(processingInterval = value))
      case "--redis-host" :: value :: tail => parseArgs(tail, current.copy(redisHost = value))
      case "--redis-port" :: value :: tail => parseArgs(tail, current.copy(redisPort = value.toInt))
      case "--redis-database" :: value :: tail => parseArgs(tail, current.copy(redisDatabase = value.toInt))
      case "--redis-key-prefix" :: value :: tail => parseArgs(tail, current.copy(redisKeyPrefix = value))
      case "--redis-alert-threshold-percent" :: value :: tail => parseArgs(tail, current.copy(redisAlertThresholdPercent = value.toDouble))
      case "--redis-latest-record-limit" :: value :: tail => parseArgs(tail, current.copy(redisLatestRecordLimit = value.toInt))
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
        |  --processing-interval <duration> Streaming trigger interval, default 10 minutes
        |  --redis-host <host>              Redis host, default 127.0.0.1
        |  --redis-port <port>              Redis port, default 6379
        |  --redis-database <db>            Redis database index, default 0
        |  --redis-key-prefix <prefix>      Redis key prefix, default agri:realtime
        |  --redis-alert-threshold-percent <percent>
        |                                  Alert threshold compared with last batch baseline, default 20.0
        |  --redis-latest-record-limit <n>  Latest records stored in Redis, default 200
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

  private def productRegionField(productName: String, region: String): String = {
    s"${Option(productName).getOrElse("")}|${Option(region).getOrElse("")}"
  }

  private def productRegionStatJson(stat: ProductRegionStat): String = {
    jsonObject(
      Seq(
        "product_name" -> jsonString(stat.productName),
        "region" -> jsonString(stat.region),
        "record_count" -> stat.recordCount.toString,
        "average_price" -> formatDouble(stat.averagePrice),
        "min_price" -> formatDouble(stat.minPrice),
        "max_price" -> formatDouble(stat.maxPrice)
      )
    )
  }

  private def priceAlertJson(alert: PriceAlert): String = {
    jsonObject(
      Seq(
        "product_name" -> jsonString(alert.productName),
        "region" -> jsonString(alert.region),
        "previous_average_price" -> formatDouble(alert.previousAveragePrice),
        "current_average_price" -> formatDouble(alert.currentAveragePrice),
        "change_rate_percent" -> formatDouble(alert.changeRatePercent),
        "alert_level" -> jsonString(alert.alertLevel),
        "batch_id" -> alert.batchId.toString,
        "detected_at" -> jsonString(alert.detectedAt)
      )
    )
  }

  private def jsonObject(fields: Seq[(String, String)]): String = {
    fields.map { case (name, value) => s"${jsonString(name)}:$value" }.mkString("{", ",", "}")
  }

  private def jsonString(value: String): String = {
    val escaped = Option(value).getOrElse("").flatMap {
      case '"' => "\\\""
      case '\\' => "\\\\"
      case '\b' => "\\b"
      case '\f' => "\\f"
      case '\n' => "\\n"
      case '\r' => "\\r"
      case '\t' => "\\t"
      case char if Character.isISOControl(char) => f"\\u${char.toInt}%04x"
      case char => char.toString
    }
    "\"" + escaped + "\""
  }

  private def jsonNullableDouble(value: Option[Double]): String = {
    value.map(formatDouble).getOrElse("null")
  }

  private def formatDouble(value: Double): String = {
    String.format(Locale.US, "%.2f", Double.box(value))
  }

  private def roundDouble(value: Double): Double = {
    BigDecimal(value).setScale(2, BigDecimal.RoundingMode.HALF_UP).toDouble
  }

  private def toDoubleOption(value: String): Option[Double] = {
    try {
      Some(value.toDouble)
    } catch {
      case _: NumberFormatException => None
    }
  }
}