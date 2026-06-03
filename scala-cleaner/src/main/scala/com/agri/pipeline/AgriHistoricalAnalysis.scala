package com.agri.pipeline

import org.apache.spark.sql.expressions.Window
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types.DoubleType
import org.apache.spark.sql.{DataFrame, SaveMode, SparkSession}

object AgriHistoricalAnalysis {
  private val DefaultPricePath = "/agri_price/processed/processed_price.csv"
  private val DefaultWeatherPath = "/agri_price/processed/processed_weather.csv"
  private val DefaultMergedPath = "/agri_price/processed/merged_data.csv"
  private val DefaultOutputPath = "/agri_price/output/analysis"

  final case class Options(
      pricePath: String = DefaultPricePath,
      weatherPath: String = DefaultWeatherPath,
      mergedPath: String = DefaultMergedPath,
      outputPath: String = DefaultOutputPath
  )

  def main(args: Array[String]): Unit = {
    val options = parseArgs(args.toList)
    val spark = SparkSession
      .builder()
      .appName("AgriHistoricalAnalysis")
      .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    val priceData = readPriceData(spark, options.pricePath).cache()
    val weatherData = readWeatherData(spark, options.weatherPath).cache()
    val mergedData = readMergedData(spark, options.mergedPath).cache()

    priceData.createOrReplaceTempView("price_data")
    weatherData.createOrReplaceTempView("weather_data")
    mergedData.createOrReplaceTempView("merged_data")

    val outputRoot = options.outputPath.stripSuffix("/")

    writeCsv(buildOverview(priceData, weatherData, mergedData), s"$outputRoot/overview")
    writeCsv(buildProductStatistics(priceData), s"$outputRoot/product_statistics")
    writeCsv(buildRegionStatistics(priceData), s"$outputRoot/region_statistics")
    writeCsv(buildRegionPriceDifference(priceData), s"$outputRoot/region_price_difference")
    writeCsv(buildYearlyTrend(priceData), s"$outputRoot/yearly_trend")
    writeCsv(buildDailyTrend(priceData), s"$outputRoot/daily_trend")
    writeCsv(buildSeasonalPriceChange(priceData), s"$outputRoot/seasonal_price_change")
    writeCsv(buildPriceRangeAnalysis(priceData), s"$outputRoot/price_range_analysis")
    writeCsv(buildVolatilityAnalysis(priceData), s"$outputRoot/volatility_analysis")
    writeCsv(buildWeatherCorrelation(mergedData), s"$outputRoot/weather_correlation")
    writeCsv(buildSparkSqlAnalysis(spark), s"$outputRoot/spark_sql_analysis")
    writeCsv(buildTopFluctuations(priceData), s"$outputRoot/top_fluctuations")

    spark.stop()
  }

  private def readCsv(spark: SparkSession, path: String): DataFrame = {
    spark.read
      .option("header", "true")
      .option("mode", "DROPMALFORMED")
      .csv(path)
  }

  private def readPriceData(spark: SparkSession, path: String): DataFrame = {
    readCsv(spark, path)
      .select(
        trim(col("product_name")).as("product_name"),
        normalizeCategory(col("product_category")).as("product_category"),
        trim(col("market_name")).as("market_name"),
        trim(col("region")).as("region"),
        to_date(col("date")).as("date"),
        numeric("highest_price").as("highest_price"),
        numeric("lowest_price").as("lowest_price"),
        numeric("average_price").as("average_price"),
        trim(col("unit")).as("unit")
      )
      .filter(col("product_name").isNotNull && col("date").isNotNull && col("average_price") > 0)
  }

  private def readWeatherData(spark: SparkSession, path: String): DataFrame = {
    readCsv(spark, path)
      .select(
        trim(col("region")).as("region"),
        to_date(col("date")).as("date"),
        numeric("average_temperature").as("average_temperature"),
        numeric("highest_temperature").as("highest_temperature"),
        numeric("lowest_temperature").as("lowest_temperature"),
        numeric("rainfall").as("rainfall"),
        numeric("humidity").as("humidity"),
        numeric("sunshine_duration").as("sunshine_duration"),
        trim(col("weather_condition")).as("weather_condition")
      )
      .filter(col("region").isNotNull && col("date").isNotNull)
  }

  private def readMergedData(spark: SparkSession, path: String): DataFrame = {
    readCsv(spark, path)
      .select(
        trim(col("product_name")).as("product_name"),
        normalizeCategory(col("product_category")).as("product_category"),
        trim(col("market_name")).as("market_name"),
        trim(col("region")).as("region"),
        to_date(col("date")).as("date"),
        numeric("average_price").as("average_price"),
        numeric("average_temperature").as("average_temperature"),
        numeric("highest_temperature").as("highest_temperature"),
        numeric("lowest_temperature").as("lowest_temperature"),
        numeric("rainfall").as("rainfall"),
        numeric("humidity").as("humidity"),
        numeric("sunshine_duration").as("sunshine_duration"),
        trim(col("weather_condition")).as("weather_condition")
      )
      .filter(col("product_name").isNotNull && col("date").isNotNull && col("average_price") > 0)
  }

  private def buildOverview(priceData: DataFrame, weatherData: DataFrame, mergedData: DataFrame): DataFrame = {
    val priceOverview = priceData.agg(
      count(lit(1)).as("price_records"),
      countDistinct(col("product_name")).as("product_count"),
      countDistinct(col("region")).as("price_region_count"),
      countDistinct(col("market_name")).as("market_count"),
      min(col("date")).as("price_min_date"),
      max(col("date")).as("price_max_date"),
      round(avg(col("average_price")), 2).as("average_price_mean"),
      round(expr("percentile_approx(average_price, 0.5)"), 2).as("average_price_median"),
      round(stddev_samp(col("average_price")), 2).as("average_price_stddev")
    )

    val weatherOverview = weatherData.agg(
      count(lit(1)).as("weather_records"),
      countDistinct(col("region")).as("weather_region_count"),
      min(col("date")).as("weather_min_date"),
      max(col("date")).as("weather_max_date")
    )

    val mergedOverview = mergedData.agg(count(lit(1)).as("price_weather_join_records"))
    priceOverview.crossJoin(weatherOverview).crossJoin(mergedOverview)
  }

  private def buildProductStatistics(priceData: DataFrame): DataFrame = {
    priceData
      .groupBy(col("product_name"), col("product_category"))
      .agg(
        count(lit(1)).as("record_count"),
        countDistinct(col("region")).as("region_count"),
        countDistinct(col("market_name")).as("market_count"),
        min(col("date")).as("min_date"),
        max(col("date")).as("max_date"),
        round(avg(col("average_price")), 2).as("mean_price"),
        round(expr("percentile_approx(average_price, 0.5)"), 2).as("median_price"),
        round(stddev_samp(col("average_price")), 2).as("stddev_price"),
        round(min(col("average_price")), 2).as("min_price"),
        round(max(col("average_price")), 2).as("max_price")
      )
      .orderBy(col("product_name"))
  }

  private def buildRegionStatistics(priceData: DataFrame): DataFrame = {
    priceData
      .groupBy(col("region"))
      .agg(
        count(lit(1)).as("record_count"),
        countDistinct(col("product_name")).as("product_count"),
        round(avg(col("average_price")), 2).as("mean_price"),
        round(expr("percentile_approx(average_price, 0.5)"), 2).as("median_price"),
        round(stddev_samp(col("average_price")), 2).as("stddev_price"),
        round(min(col("average_price")), 2).as("min_price"),
        round(max(col("average_price")), 2).as("max_price")
      )
      .orderBy(col("mean_price").desc_nulls_last)
  }

  private def buildRegionPriceDifference(priceData: DataFrame): DataFrame = {
    val productMean = priceData
      .groupBy(col("product_name"))
      .agg(round(avg(col("average_price")), 2).as("product_mean_price"))

    val regionMean = priceData
      .groupBy(col("product_name"), col("region"))
      .agg(
        count(lit(1)).as("record_count"),
        round(avg(col("average_price")), 2).as("region_mean_price"),
        round(expr("percentile_approx(average_price, 0.5)"), 2).as("region_median_price"),
        round(stddev_samp(col("average_price")), 2).as("region_stddev_price"),
        round(min(col("average_price")), 2).as("region_min_price"),
        round(max(col("average_price")), 2).as("region_max_price")
      )

    regionMean
      .join(productMean, Seq("product_name"), "left")
      .withColumn("gap_from_product_mean", round(col("region_mean_price") - col("product_mean_price"), 2))
      .withColumn(
        "gap_rate_percent",
        round(when(col("product_mean_price") > 0, col("gap_from_product_mean") / col("product_mean_price") * 100), 2)
      )
      .orderBy(col("product_name"), abs(col("gap_from_product_mean")).desc_nulls_last)
  }

  private def buildYearlyTrend(priceData: DataFrame): DataFrame = {
    val yearly = priceData
      .withColumn("year", year(col("date")))
      .groupBy(col("product_name"), col("year"))
      .agg(
        count(lit(1)).as("record_count"),
        round(avg(col("average_price")), 2).as("year_mean_price"),
        round(expr("percentile_approx(average_price, 0.5)"), 2).as("year_median_price"),
        round(stddev_samp(col("average_price")), 2).as("year_stddev_price"),
        round(min(col("average_price")), 2).as("year_min_price"),
        round(max(col("average_price")), 2).as("year_max_price")
      )

    val trendWindow = Window.partitionBy(col("product_name")).orderBy(col("year"))
    yearly
      .withColumn("previous_year_mean_price", lag(col("year_mean_price"), 1).over(trendWindow))
      .withColumn("year_price_change", round(col("year_mean_price") - col("previous_year_mean_price"), 2))
      .withColumn(
        "year_change_rate_percent",
        round(when(col("previous_year_mean_price") > 0, col("year_price_change") / col("previous_year_mean_price") * 100), 2)
      )
      .withColumn(
        "trend_direction",
        when(col("year_price_change") > 0, "up").when(col("year_price_change") < 0, "down").otherwise("flat")
      )
      .orderBy(col("product_name"), col("year"))
  }

  private def buildDailyTrend(priceData: DataFrame): DataFrame = {
    val daily = priceData
      .groupBy(col("product_name"), col("date"))
      .agg(
        count(lit(1)).as("record_count"),
        round(avg(col("average_price")), 2).as("daily_mean_price"),
        round(expr("percentile_approx(average_price, 0.5)"), 2).as("daily_median_price"),
        round(stddev_samp(col("average_price")), 2).as("daily_stddev_price")
      )

    val trendWindow = Window.partitionBy(col("product_name")).orderBy(col("date"))
    daily
      .withColumn("previous_mean_price", lag(col("daily_mean_price"), 1).over(trendWindow))
      .withColumn("price_change", round(col("daily_mean_price") - col("previous_mean_price"), 2))
      .withColumn(
        "change_rate_percent",
        round(when(col("previous_mean_price") > 0, col("price_change") / col("previous_mean_price") * 100), 2)
      )
      .withColumn(
        "trend_direction",
        when(col("price_change") > 0, "up").when(col("price_change") < 0, "down").otherwise("flat")
      )
      .orderBy(col("product_name"), col("date"))
  }

  private def buildSeasonalPriceChange(priceData: DataFrame): DataFrame = {
    priceData
      .withColumn("year", year(col("date")))
      .withColumn("season", seasonName(col("date")))
      .withColumn("season_order", seasonOrder(col("date")))
      .groupBy(col("product_name"), col("product_category"), col("region"), col("year"), col("season"), col("season_order"))
      .agg(
        count(lit(1)).as("record_count"),
        round(avg(col("average_price")), 2).as("season_mean_price"),
        round(expr("percentile_approx(average_price, 0.5)"), 2).as("season_median_price"),
        round(stddev_samp(col("average_price")), 2).as("season_stddev_price"),
        round(min(col("average_price")), 2).as("season_min_price"),
        round(max(col("average_price")), 2).as("season_max_price")
      )
      .orderBy(col("product_name"), col("region"), col("year"), col("season_order"))
      .drop("season_order")
  }

  private def buildPriceRangeAnalysis(priceData: DataFrame): DataFrame = {
    priceData
      .groupBy(col("product_name"), col("region"))
      .agg(
        count(lit(1)).as("record_count"),
        min(col("date")).as("min_date"),
        max(col("date")).as("max_date"),
        round(avg(col("average_price")), 2).as("mean_price"),
        round(expr("percentile_approx(average_price, 0.5)"), 2).as("median_price"),
        round(stddev_samp(col("average_price")), 2).as("stddev_price"),
        round(min(col("average_price")), 2).as("historical_min_price"),
        round(max(col("average_price")), 2).as("historical_max_price")
      )
      .withColumn("historical_price_range", round(col("historical_max_price") - col("historical_min_price"), 2))
      .withColumn(
        "range_rate_percent",
        round(when(col("mean_price") > 0, col("historical_price_range") / col("mean_price") * 100), 2)
      )
      .orderBy(col("historical_price_range").desc_nulls_last)
  }

  private def buildVolatilityAnalysis(priceData: DataFrame): DataFrame = {
    val daily = priceData
      .groupBy(col("product_name"), col("region"), col("date"))
      .agg(round(avg(col("average_price")), 2).as("daily_mean_price"))

    val trendWindow = Window.partitionBy(col("product_name"), col("region")).orderBy(col("date"))
    val withChange = daily
      .withColumn("previous_mean_price", lag(col("daily_mean_price"), 1).over(trendWindow))
      .withColumn(
        "change_rate_percent",
        when(col("previous_mean_price") > 0, (col("daily_mean_price") - col("previous_mean_price")) / col("previous_mean_price") * 100)
      )

    withChange
      .groupBy(col("product_name"), col("region"))
      .agg(
        count(col("change_rate_percent")).as("change_day_count"),
        round(avg(abs(col("change_rate_percent"))), 2).as("avg_abs_change_rate_percent"),
        round(max(abs(col("change_rate_percent"))), 2).as("max_abs_change_rate_percent"),
        round(stddev_samp(col("daily_mean_price")), 2).as("daily_price_stddev")
      )
      .filter(col("change_day_count") > 0)
      .orderBy(col("max_abs_change_rate_percent").desc_nulls_last)
  }

  private def buildWeatherCorrelation(mergedData: DataFrame): DataFrame = {
    mergedData
      .groupBy(col("product_name"))
      .agg(
        count(lit(1)).as("joined_record_count"),
        round(corr(col("average_price"), col("average_temperature")), 4).as("corr_price_avg_temperature"),
        round(corr(col("average_price"), col("rainfall")), 4).as("corr_price_rainfall"),
        round(corr(col("average_price"), col("humidity")), 4).as("corr_price_humidity"),
        round(corr(col("average_price"), col("sunshine_duration")), 4).as("corr_price_sunshine_duration")
      )
      .orderBy(col("product_name"))
  }

  private def buildSparkSqlAnalysis(spark: SparkSession): DataFrame = {
    spark.sql(
      """
        |SELECT
        |  product_name,
        |  region,
        |  COUNT(*) AS record_count,
        |  ROUND(AVG(average_price), 2) AS mean_price,
        |  ROUND(percentile_approx(average_price, 0.5), 2) AS median_price,
        |  ROUND(STDDEV_SAMP(average_price), 2) AS stddev_price,
        |  ROUND(AVG(average_temperature), 2) AS mean_temperature,
        |  ROUND(AVG(rainfall), 2) AS mean_rainfall,
        |  ROUND(AVG(humidity), 2) AS mean_humidity
        |FROM merged_data
        |GROUP BY product_name, region
        |ORDER BY product_name, mean_price DESC
        |""".stripMargin
    )
  }

  private def buildTopFluctuations(priceData: DataFrame): DataFrame = {
    val daily = priceData
      .groupBy(col("product_name"), col("region"), col("date"))
      .agg(round(avg(col("average_price")), 2).as("daily_mean_price"))

    val trendWindow = Window.partitionBy(col("product_name"), col("region")).orderBy(col("date"))
    daily
      .withColumn("previous_mean_price", lag(col("daily_mean_price"), 1).over(trendWindow))
      .withColumn("price_change", round(col("daily_mean_price") - col("previous_mean_price"), 2))
      .withColumn(
        "change_rate_percent",
        round(when(col("previous_mean_price") > 0, col("price_change") / col("previous_mean_price") * 100), 2)
      )
      .filter(col("change_rate_percent").isNotNull)
      .orderBy(abs(col("change_rate_percent")).desc)
      .limit(50)
  }

  private def numeric(columnName: String) = {
    regexp_replace(trim(col(columnName)), "[^0-9.\\-]", "").cast(DoubleType)
  }

  private def normalizeCategory(categoryColumn: org.apache.spark.sql.Column) = {
    val cleaned = trim(categoryColumn)
    when(cleaned === "蔬菜", "蔬菜类")
      .when(cleaned === "水果", "水果类")
      .when(cleaned === "粮食", "粮食类")
      .otherwise(cleaned)
  }

  private def seasonName(dateColumn: org.apache.spark.sql.Column) = {
    val monthValue = month(dateColumn)
    when(monthValue.between(3, 5), "春季")
      .when(monthValue.between(6, 8), "夏季")
      .when(monthValue.between(9, 11), "秋季")
      .otherwise("冬季")
  }

  private def seasonOrder(dateColumn: org.apache.spark.sql.Column) = {
    val monthValue = month(dateColumn)
    when(monthValue.between(3, 5), 1)
      .when(monthValue.between(6, 8), 2)
      .when(monthValue.between(9, 11), 3)
      .otherwise(4)
  }

  private def writeCsv(dataFrame: DataFrame, outputPath: String): Unit = {
    dataFrame
      .coalesce(1)
      .write
      .mode(SaveMode.Overwrite)
      .option("header", "true")
      .csv(outputPath)
  }

  private def parseArgs(args: List[String], current: Options = Options()): Options = {
    args match {
      case Nil => current
      case "--price-path" :: value :: tail => parseArgs(tail, current.copy(pricePath = value))
      case "--weather-path" :: value :: tail => parseArgs(tail, current.copy(weatherPath = value))
      case "--merged-path" :: value :: tail => parseArgs(tail, current.copy(mergedPath = value))
      case "--output-path" :: value :: tail => parseArgs(tail, current.copy(outputPath = value))
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
    System.err.println(
      """
        |Usage: spark-submit --class com.agri.pipeline.AgriHistoricalAnalysis target/agri-scala-cleaner-1.0.0.jar [options]
        |
        |Options:
        |  --price-path <path>    HDFS path of processed_price.csv
        |  --weather-path <path>  HDFS path of processed_weather.csv
        |  --merged-path <path>   HDFS path of merged_data.csv
        |  --output-path <path>   HDFS output directory for analysis results
        |""".stripMargin
    )
  }
}