// this is a simple: using spark mllib pipeline to solve a regression problem
//

import org.apache.log4j.{Logger}
//core and SparkSQL

import org.apache.spark.{SparkConf, SparkContext}
// Spark config

import org.apache.spark.sql.hive.HiveContext
// hive tool

import org.apache.spark.sql.DataFrame
// hive DataFrame for storing Data

import org.apache.spark.ml.feature.{StringIndexer, VectorAssembler, OneHotEncoder}
// ML Feature Creation

import org.apache.spark.ml.tuning.{ParamGridBuilder, CrossValidator}
//import org.apache.spark.ml.tuning.{ParamGridBuilder, TrainValidationSplit}
// there is no TrainValidationSplit ??
// tuning hyper parameters

import org.apache.spark.ml.evaluation.{RegressionEvaluator}
// evaluation for regression model

import org.apache.spark.ml.regression.{LinearRegression}
// regression model

import org.apache.spark.ml.Pipeline
// pipeline

import org.apache.spark.mllib.evaluation.RegressionMetrics
// evaluation for regression model


object pipeline {


val stateHolidayIndexer = new StringIndexer()
  .setInputCol("StateHoliday")
  .setOutputCol("StateHolidayIndex")
val schoolHolidayIndexer = new StringIndexer()
  .setInputCol("SchoolHoliday")
  .setOutputCol("SchoolHolidayIndex")

//Convert numerical based categorical features(in one column) to numerical continuous features 
//(one column per category) /increasing sparsity/
val stateHolidayEncoder = new OneHotEncoder()
  .setInputCol("StateHolidayIndex")
  .setOutputCol("StateHolidayVec")
val schoolHolidayEncoder = new OneHotEncoder()
  .setInputCol("SchoolHolidayIndex")
  .setOutputCol("SchoolHolidayVec")
val dayOfMonthEncoder = new OneHotEncoder()
  .setInputCol("DayOfMonth")
.setOutputCol("DayOfMonthVec")
val dayOfWeekEncoder = new OneHotEncoder()
  .setInputCol("DayOfWeek")
.setOutputCol("DayOfWeekVec")
val storeEncoder = new OneHotEncoder()
  .setInputCol("Store")
  .setOutputCol("StoreVec")

// all the features would transformed to one-hot features

//assemble all of our vectors together into one vector to input into our model.
val assembler = new VectorAssembler()
  .setInputCols(Array(
              "StoreVec", 
              "DayOfWeekVec", 
              "Open",
              "DayOfMonthVec", 
              "StateHolidayVec", 
              "SchoolHolidayVec"
            )
        )
  .setOutputCol("features")



//------------------------------------ Creating the Pipelines -------------------------------------
/*Much like the DAG that we saw in the the core concepts of the Pipeline:
Transformer: 
A Transformer is an algorithm which can transform one DataFrame into another DataFrame.
E.g., an ML model is a Transformer which transforms DataFrame with features into a DataFrame with predictions.
Estimator: 
An Estimator is an algorithm which can be fit on a DataFrame to produce a Transformer. 
E.g., a learning algorithm is an Estimator which trains on a DataFrame and produces a model.
Pipeline: 
A Pipeline chains multiple Transformers and Estimators together to specify an ML workflow.
*/

/*
Once you see the code, you'll notice that in our train test split we're also setting an Evaluatorthat 
will judge how well our model is doing and automatically select the best parameter for us to use based 
on that metric. This means that we get to train lots and lots of different models to see which one is best. 
Super simple! Let's walk through the creation for each model.
*/

// this is a pipeline which can cerate new features and train the model and tune the parameters
// finally , this pipeline would give us a model with best parameters 
def preppedLRPipeline():CrossValidator = {
  val lr = new LinearRegression()

  val paramGrid = new ParamGridBuilder()  // parameters to tune
    .addGrid(lr.regParam, Array(0.1, 0.01))
    //.addGrid(lr.fitIntercept)
    .addGrid(lr.elasticNetParam, Array(0.0, 0.25, 0.5, 0.75, 1.0))
    .build()

  val pipeline = new Pipeline()
    .setStages(Array(                   // put all the preprocessing before and model into the pipeline
            stateHolidayIndexer, 
            schoolHolidayIndexer,
              stateHolidayEncoder, 
              schoolHolidayEncoder, 
              storeEncoder,
              dayOfWeekEncoder, 
              dayOfMonthEncoder,
              assembler, 
              lr  // the last thing is the model
              )
        )

  val tvs = new CrossValidator()  // put the [preprocessing, model], Evaluator, tuning, paramgrid together
    .setEstimator(pipeline) // here is something can be fit
    .setEvaluator(new RegressionEvaluator) //here is a model Evaluator
    .setEstimatorParamMaps(paramGrid) // here is the hyper parameters to tune
    .setNumFolds(4) 

  tvs  // return the model with best parameters
}


// ---------------------load the data using hive --------------------
// use the hive select tool to get the data from file

// train data
def loadTrainingData(sqlContext:HiveContext):DataFrame = {  //return a DataFrame
  val trainRaw = sqlContext
    .read.format("com.databricks.spark.csv") 
    .option("header", "true")
    .load("~/workspace/kaggle_rossmann/train.csv")
    .repartition(6)

  trainRaw.registerTempTable("raw_training_data")

  sqlContext.sql("""SELECT 
                double(Sales) label, 
                double(Store) Store, 
                int(Open) Open, 
                double(DayOfWeek) DayOfWeek,
                StateHoliday, 
                SchoolHoliday, 
                (double(regexp_extract(Date, '\\d+-\\d+-(\\d+)', 1))) DayOfMonth
            FROM raw_training_data
          """).na.drop()
}


// test data
def loadKaggleTestData(sqlContext:HiveContext) = {
  val testRaw = sqlContext //testRaw is stored in the table which can be selected
    .read.format("com.databricks.spark.csv")
    .option("header", "true")
    .load("~/workspace/kaggle_rossmann/test.csv")
    .repartition(6)

  testRaw.registerTempTable("raw_test_data")

  val testData = sqlContext.sql("""SELECT
                      Id, 
                      double(Store) Store, int(Open) Open, 
                      double(DayOfWeek) DayOfWeek, 
                      StateHoliday,
                      SchoolHoliday, 
                      (double(regexp_extract(Date, '\\d+-\\d+-(\\d+)', 1))) DayOfMonth
                    FROM raw_test_data
                    WHERE !(
                        ISNULL(Id) OR 
                        ISNULL(Store) OR 
                        ISNULL(Open) OR 
                        ISNULL(DayOfWeek) OR 
                        ISNULL(StateHoliday) OR 
                        ISNULL(SchoolHoliday)
                      )
                  """).na.drop() // weird things happen if you don't filter out the null values manually

  Array(testRaw, testData)  //return something,testRaw is the data(table) from the file, testData is the data selected from table
  // got to hold onto testRaw so we can make sure
  // to have all the prediction IDs to submit to kaggle
}



// -------------------- save predictions --------------------------------------
def savePredictions(predictions:DataFrame, testRaw:DataFrame) = {
  val tdOut = testRaw
    .select("Id") // select the colunms of "Id"
    //.distinct()
    .join(predictions, testRaw("Id") === predictions("PredId"), "outer") // combine acorrding to id
    .select("Id", "Sales")
    .na.fill(0:Double) // some of our inputs were null so we have to
                       // fill these with something
  tdOut
    .coalesce(1) //no shuffle,put it into onr block
    .write.format("com.databricks.spark.csv")
    .option("header", "true")
    .save("~/workspace/kaggle_rossmann/linear_regression_predictions.csv")
}


// ------Fitting, Testing, and Using The Model-------------------------
/*
Now we've brought in our data, created our pipeline, 
we are now ready to train up our models and see how they perform. 
This will take some time to run because we are exploring a 
hyperparameter space for each model. It takes time to try out all 
the permutations in our parameter grid as well as create a training 
set for each tree so be patient!
*/
def fitModel(tvs:CrossValidator, data:DataFrame) = {
  val Array(training, test) = data.randomSplit(Array(0.8, 0.2), seed = 12345)
  // get the train data and test data

  println("Fitting data")
  val model = tvs.fit(training) // fit the model using tvs(a pipeline)(including tunning hyperparameters !)

  println("Now performing test on hold out set")
  val holdout = model.transform(test).select("prediction","label") // result of test

  // have to do a type conversion for RegressionMetrics
  val rm = new RegressionMetrics(holdout.rdd.map(x =>
    (x(0).asInstanceOf[Double], x(1).asInstanceOf[Double])))

  println("Test Metrics")
  println("Test Explained Variance:")
  println(rm.explainedVariance)
  println("Test R^2 Coef:")
  println(rm.r2)
  println("Test MSE:")
  println(rm.meanSquaredError)
  println("Test RMSE:")
  println(rm.rootMeanSquaredError)

  model //return the model with best parameters 
}



def main(args: Array[String]): Unit = {

//val conf = new SparkConf().setAppName("pipeline_regression")
val sc = new SparkContext(new SparkConf().setAppName("App").setMaster("local[4]"))
val sqlContext = new HiveContext(sc)

//---------------- some method of transform and creatation of new features -----------------------
// we need a input column name and output column name
//Convert string based categorical features to numerical categorical features

// ================== main step ======================
val data = loadTrainingData(sqlContext)
// get the training data

val Array(testRaw, testData) = loadKaggleTestData(sqlContext)
// get the test data

val linearTvs = preppedLRPipeline()
// The linear Regression Pipeline

println("evaluating linear regression")
val lrModel = fitModel(linearTvs, data)

println("Generating kaggle predictions")
val lrOut = lrModel.transform(testData) // transform is predicting in the sklearn
  .withColumnRenamed("prediction","Sales") //rename the column
  .withColumnRenamed("Id","PredId")
  .select("PredId", "Sales")

println("Saving kaggle predictions")

savePredictions(lrOut, testRaw)

}



}
