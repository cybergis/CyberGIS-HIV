#clear environment history
rm(list = ls())
gc()

library("reshape2")

dir <- paste0(getwd(), "/")
dir.data <- paste0(dir, "Data/")
dir.results <- '/home/jovyan/shared_data/data/hiv/' # Keeling directory that has "saved_results.rda"
source(paste0(dir, "Functions_Formatting.R"))
setwd(dir)

#FIPS_list = NULL
#var_names = NULL
#var_muls = NULL

forecast_func <- function(FIPS_list = NULL, var_names = NULL, var_muls = NULL, var_file = "data_imputedx_forecast.csv") {
  # load saved models for part 1 and also forecast datasets
  start_time <- Sys.time()
  load(paste0(dir.results, "saved_results.rda"))
  zero.model <- results$zero.model
  pred.model <- results$pred.model

  # load the data with imputed x and factorize variables
  data_imputedx <- read.csv(paste0(dir.data, var_file))

  # keep the input FIPS codes
  if (!is.null(FIPS_list)) {
    data_imputedx = dplyr::filter(data_imputedx, FIPS %in% FIPS_list)
  }

  # change the value of x variables
  if (!is.null(var_names)) {
    var_names = unlist(var_names)
    var_muls = unlist(var_muls)
    for (i in 1:length(var_names)) {
      data_imputedx[, var_names[i]] <- data_imputedx[, var_names[i]] * var_muls[i]
    }
  }

  # transform data
  data_imputedx <- data.transform(data_imputedx)
  data_imputedx$Year <- data_imputedx$Year + 1

  # factorize discrete vars
  factorLst <- c("FederalRegionCode", "CensusRegionCode", "urbanizationizationlevel", "Hidden_AR3", "Hidden_AR2", "Hidden_AR1",
                 "Hidden", "Binary_AR3", "Binary_AR2", "Binary_AR1", "Binary")
  for (i in factorLst) {
    data_imputedx[, i] <- as.factor(data_imputedx[, i])
  }

  # forecasting loop
  thres <- 0.3
  beg_year <- 2022
  end_year <- 2026
  for (i in seq(beg_year, end_year, by = 1)) {
    # predict zero
    data_imputedx_y <- subset(data_imputedx, Year == i)
    pred.zero.raw <- predict(zero.model, data_imputedx_y, type = 'response')
    pred.zero.bin <- ifelse(pred.zero.raw > thres, 1, 0)
    pred.zero <- ifelse(pred.zero.raw > thres, pred.zero.raw, 0)

    # predict gee
    pred.one.raw <- exp(predict(pred.model, data_imputedx_y))
    pred.one.raw <- ifelse(pred.one.raw < 0, 0, pred.one.raw)

    # combine both steps
    pred <- round(pred.zero * pred.one.raw, 1)

    # combine both steps
    data.full <- subset(data_imputedx, select = -c(LogRate, Hidden, Binary))
    data.full.y <- subset(data.full, Year == i)

    # fill the predicted values in original dataset
    data.full.y$LogRate <- log(pred + 1)
    data.full.y$Binary <- pred.zero.bin
    # suppressed data
    data.full.y$Hidden <- ifelse(pred < 4.5 * 100000 / data.full.y$population, 1, 0)
    data.full.y$Hidden <- ifelse(pred <= 0, 0, data.full.y$Hidden)


    # merge to data_forecast
    data_imputedx <- merge(data_imputedx, data.full.y[c("FIPS", "Year", "LogRate", "Binary", "Hidden")], by = c("FIPS", "Year"), all = TRUE)
    data_imputedx$Hidden.y <- as.factor(data_imputedx$Hidden.y)
    data_imputedx$Binary.y <- as.factor(data_imputedx$Binary.y)

    # combine merge conflicts into the correct variables and drop extra merge columns
    data_imputedx$LogRate <- ifelse(is.na(data_imputedx$LogRate.y), data_imputedx$LogRate.x, data_imputedx$LogRate.y)
    data_imputedx$Binary <- ifelse(is.na(data_imputedx$Binary.y), data_imputedx$Binary.x, data_imputedx$Binary.y)
    data_imputedx$Hidden <- ifelse(is.na(data_imputedx$Hidden.y), data_imputedx$Hidden.x, data_imputedx$Hidden.y)
    data_imputedx$Binary <- as.factor(data_imputedx$Binary - 1) # for some reason, we need to deduct 1 to make the ifelse work
    data_imputedx$Hidden <- as.factor(data_imputedx$Hidden - 1)
    data_imputedx <- subset(data_imputedx, select = -c(LogRate.x, LogRate.y, Binary.x, Binary.y, Hidden.x, Hidden.y))


    # update AR1 for the next year
    data_imputedx_AR1 <- data_imputedx[c("FIPS", "Year", "LogRate", "Hidden", "Binary")]
    data_imputedx_AR1$Year <- data_imputedx_AR1$Year + 1
    names(data_imputedx_AR1)[names(data_imputedx_AR1) == "LogRate"] <- "LogRate_AR1"
    names(data_imputedx_AR1)[names(data_imputedx_AR1) == "Binary"] <- "Binary_AR1"
    names(data_imputedx_AR1)[names(data_imputedx_AR1) == "Hidden"] <- "Hidden_AR1"

    data_imputedx <- merge(data_imputedx, data_imputedx_AR1, by = c("FIPS", "Year"), all = TRUE)
    data_imputedx <- subset(data_imputedx, Year <= (end_year + 1))
    data_imputedx$LogRate_AR1 <- ifelse(data_imputedx$Year != (i + 1), data_imputedx$LogRate_AR1.x, data_imputedx$LogRate_AR1.y)
    data_imputedx$Binary_AR1 <- ifelse(data_imputedx$Year != (i + 1), data_imputedx$Binary_AR1.x, data_imputedx$Binary_AR1.y)
    data_imputedx$Hidden_AR1 <- ifelse(data_imputedx$Year != (i + 1), data_imputedx$Hidden_AR1.x, data_imputedx$Hidden_AR1.y)
    data_imputedx$Binary_AR1 <- as.factor(data_imputedx$Binary_AR1 - 1) # for some reason, we need to deduct 1 to make the ifelse work
    data_imputedx$Hidden_AR1 <- as.factor(data_imputedx$Hidden_AR1 - 1)
    data_imputedx <- subset(data_imputedx, select = -c(LogRate_AR1.x, LogRate_AR1.y, Binary_AR1.x, Binary_AR1.y, Hidden_AR1.x, Hidden_AR1.y))


    # update AR2 for the next year
    data_imputedx_AR2 <- data_imputedx[c("FIPS", "Year", "LogRate", "Hidden", "Binary")]
    data_imputedx_AR2$Year <- data_imputedx_AR2$Year + 2
    names(data_imputedx_AR2)[names(data_imputedx_AR2) == "LogRate"] <- "LogRate_AR2"
    names(data_imputedx_AR2)[names(data_imputedx_AR2) == "Binary"] <- "Binary_AR2"
    names(data_imputedx_AR2)[names(data_imputedx_AR2) == "Hidden"] <- "Hidden_AR2"

    data_imputedx <- merge(data_imputedx, data_imputedx_AR2, by = c("FIPS", "Year"), all = TRUE)
    data_imputedx = subset(data_imputedx, Year <= (end_year + 1))
    data_imputedx$LogRate_AR2 <- ifelse(data_imputedx$Year != (i + 2), data_imputedx$LogRate_AR2.x, data_imputedx$LogRate_AR2.y)
    data_imputedx$Binary_AR2 <- ifelse(data_imputedx$Year != (i + 2), data_imputedx$Binary_AR2.x, data_imputedx$Binary_AR2.y)
    data_imputedx$Hidden_AR2 <- ifelse(data_imputedx$Year != (i + 2), data_imputedx$Hidden_AR2.x, data_imputedx$Hidden_AR2.y)
    data_imputedx$Binary_AR2 <- as.factor(data_imputedx$Binary_AR2 - 1) # for some reason, we need to deduct 1 to make the ifelse work
    data_imputedx$Hidden_AR2 <- as.factor(data_imputedx$Hidden_AR2 - 1)
    data_imputedx <- subset(data_imputedx, select = -c(LogRate_AR2.x, LogRate_AR2.y, Binary_AR2.x, Binary_AR2.y, Hidden_AR2.x, Hidden_AR2.y))

    # update AR3 for the next year
    data_imputedx_AR3 <- data_imputedx[c("FIPS", "Year", "LogRate", "Hidden", "Binary")]
    data_imputedx_AR3$Year <- data_imputedx_AR3$Year + 2
    names(data_imputedx_AR3)[names(data_imputedx_AR3) == "LogRate"] <- "LogRate_AR3"
    names(data_imputedx_AR3)[names(data_imputedx_AR3) == "Binary"] <- "Binary_AR3"
    names(data_imputedx_AR3)[names(data_imputedx_AR3) == "Hidden"] <- "Hidden_AR3"

    data_imputedx <- merge(data_imputedx, data_imputedx_AR3, by = c("FIPS", "Year"), all = TRUE)
    data_imputedx = subset(data_imputedx, Year <= (end_year + 1))
    data_imputedx$LogRate_AR3 <- ifelse(data_imputedx$Year != (i + 2), data_imputedx$LogRate_AR3.x, data_imputedx$LogRate_AR3.y)
    data_imputedx$Binary_AR3 <- ifelse(data_imputedx$Year != (i + 2), data_imputedx$Binary_AR3.x, data_imputedx$Binary_AR3.y)
    data_imputedx$Hidden_AR3 <- ifelse(data_imputedx$Year != (i + 2), data_imputedx$Hidden_AR3.x, data_imputedx$Hidden_AR3.y)
    data_imputedx$Binary_AR3 <- as.factor(data_imputedx$Binary_AR3 - 1) # for some reason, we need to deduct 1 to make the ifelse work
    data_imputedx$Hidden_AR3 <- as.factor(data_imputedx$Hidden_AR3 - 1)
    data_imputedx <- subset(data_imputedx, select = -c(LogRate_AR3.x, LogRate_AR3.y, Binary_AR3.x, Binary_AR3.y, Hidden_AR3.x, Hidden_AR3.y))
  }

  # save data_imputedx with forecasted HIV rates
  data_imputedx$Year <- data_imputedx$Year - 1
  data_imputedx$Rate <- exp(data_imputedx$LogRate_AR1) - 1
  # write.csv(data_imputedx, paste0(dir.data, "data_long.csv"), row.names = FALSE)


  # suppress small cases
  #data_imputedx$Cases <- round(data_imputedx$Rate * exp(data_imputedx$PopEstimate) / 100000, 0)
  #data_imputedx$Rate[data_imputedx$Cases <= 4 & data_imputedx$Cases >= 1] = "Suppressed"
  #data_imputedx <- subset(data_imputedx, select = -c(Cases))

  # keep handfull of vars
  selected_cols = c("FIPS", "Year", "Rate",
                    "opioid_prsc",
                    "FoodStampSNAPRecipientEstimate_r",
                    "PopinJuvenilleFacilities_r_l",
                    "nFedQualifiedHealthCenters_r_l",
                    "nNHSCPrimaryCareSiteswProv_r_l",
                    "knowledge",
                    "hcv",
                    "hivtst",
                    "nCommunityMentalHealthCtrs_r_l",
                    "prep_rate_l",
                    "HHswSupplemntlSecurityInc_r",
                    "illicit_l",
                    "linkage")
  data_imputedx_sub <- data_imputedx[selected_cols]


  ###############
  # convert the code to wide format
  remove <- c("FIPS", "Year", "FederalRegionCode", "CensusRegionCode")
  all_cols <- selected_cols
  wide_col_names <- all_cols[!(all_cols %in% remove)]

  data_wide <- reshape(data_imputedx_sub,
                       idvar = "FIPS",
                       v.names = wide_col_names,
                       timevar = "Year",
                       direction = "wide")


  # reorder columns
  data_wide <- data_wide[, order(colnames(data_wide))]
  rate_cols <- c()
  for (c in colnames(data_wide)) {
    if (grepl("Rate", c)) {
      rate_cols <- append(rate_cols, which(colnames(data_wide) == c))
    }
  }
  data_wide <- data_wide[, c(rate_cols, order(colnames(data_wide))[!(order(colnames(data_wide)) %in% rate_cols)])]
  data_wide <- data_wide[, c(which(colnames(data_wide) == "FIPS"), which(colnames(data_wide) != "FIPS"))]

  #write.csv(data_wide, paste0(dir.data, "data_wide.csv"), row.names = FALSE)
  end_time <- Sys.time()
  print(end_time - start_time)
  return(data_wide)
}

#
# start_time <- Sys.time()
# data_wide <- forecast_func()
# end_time <- Sys.time()
# end_time - start_time
#
# data_wide2 = forecast_func(
#   var_names = c("opioid_prsc",
#                 "FoodStampSNAPRecipientEstimate_r",
#                 "PopinJuvenilleFacilities_r_l",
#                 "nFedQualifiedHealthCenters_r_l",
#                 "nNHSCPrimaryCareSiteswProv_r_l",
#                 "knowledge",
#                 "hcv",
#                 "hivtst",
#                 "nCommunityMentalHealthCtrs_r_l",
#                 "prep_rate_l",
#                 "HHswSupplemntlSecurityInc_r",
#                 "illicit_l",
#                 "linkage"
#   ),
#   var_muls = c(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1))
# data_wide2$Rate.2026 - data_wide$Rate.2026

# opioid_prsc PopinJuvenilleFacilities_r_l nNHSCPrimaryCareSiteswProv_r_l nCommunityMentalHealthCtrs_r_l