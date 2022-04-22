#match variables and HIV rates
arrange.data <- function(data){
  defaultW <- getOption("warn")
  options(warn = -1)

  data[,"Rate_AR1"] <- as.numeric(as.character(data[, "hiv_rate"]) )
  data <- data[ , !(names(data) %in% c("hiv_rate"))]
  data$Rate_AR1 <- ifelse(data$population<115, 0,data$Rate_AR1)

  #Add hidden AR1
  data$Hidden_AR1 <- ifelse(is.na(data$Rate_AR1), 1, 0)
  #Add binary AR1
  data$Binary_AR1 <- ifelse(data$Rate_AR1>0 | is.na(data$Rate_AR1), 1, 0)

  options(warn = defaultW)
  return(data)
}

#Add HIV autoregressive covariates
rates.lag<- function(data){
  defaultW <- getOption("warn")
  options(warn = -1)
  # update AR2 for the next year
  tmp <- data[c("FIPS","Year", "Rate_AR1", "Hidden_AR1", "Binary_AR1")]
  tmp$Year <- tmp$Year+1
  names(tmp)[names(tmp) == "Rate_AR1"] <- "Rate_AR2"
  names(tmp)[names(tmp) == "Binary_AR1"] <- "Binary_AR2"
  names(tmp)[names(tmp) == "Hidden_AR1"] <- "Hidden_AR2"

  data<-merge(data, tmp, by=c("FIPS","Year"), all = TRUE)
  data <- subset(data, Year<=2021)

  # update AR3 for the next year
  tmp <- data[c("FIPS","Year", "Rate_AR1", "Hidden_AR1", "Binary_AR1")]
  tmp$Year <- tmp$Year+2
  names(tmp)[names(tmp) == "Rate_AR1"] <- "Rate_AR3"
  names(tmp)[names(tmp) == "Binary_AR1"] <- "Binary_AR3"
  names(tmp)[names(tmp) == "Hidden_AR1"] <- "Hidden_AR3"

  data<-merge(data, tmp, by=c("FIPS","Year"), all = TRUE)
  data <- subset(data, Year<=2021)

  # update rate for the next year
  tmp <- data[c("FIPS","Year", "Rate_AR1", "Hidden_AR1", "Binary_AR1")]
  tmp$Year <- tmp$Year-1
  names(tmp)[names(tmp) == "Rate_AR1"] <- "Rate"
  names(tmp)[names(tmp) == "Binary_AR1"] <- "Binary"
  names(tmp)[names(tmp) == "Hidden_AR1"] <- "Hidden"

  data<-merge(data, tmp, by=c("FIPS","Year"), all = TRUE)
  data <- subset(data, Year>=2012)
  data <- subset(data, Year<=2020)

  options(warn = defaultW)
  return(data)
}


#Impute suppressed HIV rates
impute.suppressed <- function(data, sim=100){
  defaultW <- getOption("warn")
  options(warn = -1)
  data.orig = data
  data$Cases <- round(data$Rate*data$population/100000,0)
  data$Cases_AR1 <- round(data$Rate_AR1*data$population/100000,0)
  data$Cases_AR2 <- round(data$Rate_AR2*data$population/100000,0)
  data$Cases_AR3 <- round(data$Rate_AR3*data$population/100000,0)
  var <- c("Cases","Cases_AR1","Cases_AR2","Cases_AR3")
  
  data.MNAR = data
  #for(i in 1:ncol(data.MNAR)) data.MNAR[,i]=as.numeric(as.character(data.MNAR[,i])) #convert each column to numeric
  set.seed(100)
  MNAR <- MNAR1 <- MNAR2 <- MNAR3 <- matrix(NA,nrow=length(data.MNAR[,1]), ncol=sim)
  for(j in 1:sim){
    imp1 = impute.TPois(data.MNAR, var, tune.sigma = 2.2) #Can adjust tune.sigma
    MNAR[,j] = imp1$Cases
    MNAR1[,j] = imp1$Cases_AR1
    MNAR2[,j] = imp1$Cases_AR2
    MNAR3[,j] = imp1$Cases_AR3
  }
  Rate <- Rate_AR1 <- Rate_AR2 <- Rate_AR3 <- vector()
  for(i in 1:length(data$FIPS)){
    fips = data[i,"FIPS"]
    yr = data[i,"Year"]
    ar0 = subset(data, FIPS == fips & Year == yr+1)
    ar1 = subset(data, FIPS == fips & Year == yr)
    ar2 = subset(data, FIPS == fips & Year == yr-1)
    ar3 = subset(data, FIPS == fips & Year == yr-2)
    #if year unavailable use next year population
    pop1 = ar1$population
    pop0 = ifelse(length(ar0$FIPS)==0, pop1, ar0$population )
    pop2 = ifelse(length(ar2$FIPS)==0, pop1, ar2$population )
    pop3 = ifelse(length(ar3$FIPS)==0, pop2, ar3$population )
    
    #Transform cases to rate
    Rate[i] = round( round(mean(MNAR[i,]),0)*100000/pop0, 4)
    Rate_AR1[i] = round( round(mean(MNAR1[i,]),0)*100000/pop1, 4)
    Rate_AR2[i] = round( round(mean(MNAR2[i,]),0)*100000/pop2, 4)
    Rate_AR3[i] = round( round(mean(MNAR3[i,]),0)*100000/pop3, 4)
    }
  
  data.orig$Rate <- ifelse(is.na(data.orig$Rate), Rate, data.orig$Rate)
  data.orig$Rate_AR1 <- ifelse(is.na(data.orig$Rate_AR1), Rate_AR1, data.orig$Rate_AR1)
  data.orig$Rate_AR2 <- ifelse(is.na(data.orig$Rate_AR2), Rate_AR2, data.orig$Rate_AR2)
  data.orig$Rate_AR3 <- ifelse(is.na(data.orig$Rate_AR3), Rate_AR3, data.orig$Rate_AR3)
  options(warn = defaultW)
  return(data.orig)
}

#Function for quantile imputation
impute.TPois <- function(dataSet, var, tune.sigma = 2) {
  nFeatures = dim(dataSet)[1]
  dataSet.imputed = dataSet
  QR.obj = list()
  nSamples = na.omit(match(var,colnames(dataSet)))
  
  for (i in nSamples) {
    curr.sample = dataSet[, i]
    pNAs = length(which(is.na(curr.sample)))/length(curr.sample)
    upper.q = 0.95
    q.pois = qpois(seq(pNAs, upper.q, (upper.q-pNAs)/(upper.q*10000)),lambda=tune.sigma)
    
    q.curr.sample = quantile(curr.sample, probs = seq(0, upper.q, 1e-04), na.rm = T)
    temp.QR = glm(q.curr.sample ~ q.pois, family = poisson())
    QR.obj[[i]] = temp.QR
    mean.CDD = temp.QR$coefficients[1]
    sd.CDD = as.numeric(temp.QR$coefficients[2])
    data.to.imp = rtpois(n=nFeatures, lambda=sd.CDD * tune.sigma, a=0, b = qpois(pNAs, lambda = sd.CDD * tune.sigma))
    
    curr.sample.imputed = curr.sample
    curr.sample.imputed[which(is.na(curr.sample))] = data.to.imp[which(is.na(curr.sample))]
    dataSet.imputed[, i] = curr.sample.imputed
  }
  return(dataSet.imputed)
}

#Function for x variable imputation
data.clean <- function(data.tmp){
  defaultW <- getOption("warn")
  options(warn = -1)

  # drop extra columns -- all other variables other than FIPS and year are X or y variables
  drops <- c("StateName", "State", "CountyName", "CountyNameStateAbbrev", "FIPSStateCode", "FIPSCountyCode", "NumberHHs")
  data.tmp <- data.tmp[, !(names(data.tmp) %in% drops)]

  ##################################################################################################
  #remove any variables missing too much data (more than 25%)
  count.tmp <-  vector()
  for(i in 1:ncol(data.tmp)){
    count.tmp[i] <- sum(is.na(data.tmp[,i]))
  }
  remove <- which(count.tmp>length(data.tmp[,1])*.25)
  prep_id <- which( colnames(data.tmp)=="prep_rate_l" )
  remove <- remove[remove != prep_id]

  if(length(remove) != 0){
    data.tmp <- subset(data.tmp, select = -c(remove))
  }

  #####################################################################
  ##################################################################################################
  ##Impute data
  t = data.tmp
  data.info = data.tmp[ ,(names(data.tmp) %in% c("FIPS","Year")) ]
  data.impute = data.tmp[ ,!(names(data.tmp) %in% c("FIPS","Year"))]
  
  for(i in 1:ncol(data.impute)) data.impute[,i]=as.numeric(as.character(data.impute[,i])) #convert each column to factor
  
  tmp <- BNDataset(data.impute, discreteness = c(rep(FALSE,length(data.impute[1,])) ),
                   variables = colnames(data.impute), 
                   node.sizes = c(rep(10,length(data.impute[1,]))),
                   starts.from = 1)
  imputed <- bnstruct::impute(tmp)
  data.impute <- as.data.frame(imputed@imputed.data)
  data.tmp <- cbind(data.info, data.impute)

  #Transform rate to log
  data.tmp$LogRate_AR3 <- log(data.tmp$Rate_AR3+1)
  data.tmp$LogRate_AR2 <- log(data.tmp$Rate_AR2+1)
  data.tmp$LogRate_AR1 <- log(data.tmp$Rate_AR1+1)
  data.tmp$LogRate <- log(data.tmp$Rate+1)
  
  ####################################################################
  #remove informative columns not used in model building
  data.tmp <- subset(data.tmp, select = -c(Rate_AR3))
  data.tmp <- subset(data.tmp, select = -c(Rate_AR2))
  data.tmp <- subset(data.tmp, select = -c(Rate_AR1))
  
  #####################################################################
  #convert categorical data to factors
  
  #'discrete' needs to be defined in 'Final_Results.R' file
  add <- c("Hidden_AR3", "Hidden_AR2","Hidden_AR1","Hidden","Binary_AR3","Binary_AR2","Binary_AR1","Binary")
  
  reorder <- match(c(discrete,add), names(data.tmp))
  reorder <- na.omit(reorder)
  for (i in reorder){
    data.tmp[,i] = as.factor(data.tmp[,i])
  }

  ####################################################################
  # fix state level variables to be same among all counties
  state_level_vars <- c("illicit_l", "marijuana_l", "marijuana_init_l", "cocaine_l", "alcohol_l", "tobacco_l", "cigar_l",
      "mental_severe_l", "mental_l", "suicide_l", "depress_l", "knowledge", "linkage", "suppression_per", "hivmedic_per")
  agg_data_stcols <- append(c("SFIPS", "Year"), state_level_vars)
  agg_data_cntycols <- append(c("FIPS", "Year"), state_level_vars)
  agg_data <- data.tmp[ , (names(data.tmp) %in% c(agg_data_cntycols))]
  agg_data$SFIPS <- round(agg_data$FIPS / 1000 , 0)
  data.tmp$SFIPS <- round(data.tmp$FIPS / 1000 , 0)
  agg_data <- aggregate(agg_data,
                        by = list(agg_data$SFIPS, agg_data$Year),
                        FUN = median)[agg_data_stcols]
  data.tmp <- merge(data.tmp[ , !(names(data.tmp) %in% c(state_level_vars))],
                               agg_data,by=c("SFIPS","Year"))
  data.tmp <- subset(data.tmp, select = -c(SFIPS))

  options(warn = defaultW)
  return(data.tmp = data.tmp)
}

#add any log, sqrt or scaling transformations here
data.transform = function(data.tmp){
  #TRANSFORM DATA
  #must have variable population with log transform!! (It is used in model prediction otherwise you would need to adjust how it is specified in model.)
  data.tmp$population = log(data.tmp$population)

  return(data.tmp)
}

#Can remove data that is too highly correlated to help save time in variable selection
data.correlated = function(data.tmp){
  fix <- c("FIPS","Year","Rate","Rate_AR1","Rate_AR2","Rate_AR3","Hidden","Hidden_AR1","Hidden_AR2","Hidden_AR3","Binary","Binary_AR1","Binary_AR2","Binary_AR3")
  reorder <- match(fix, names(data.tmp))
  reorder <- na.omit(reorder)
  data.tmp2 <- data.tmp[,-c(reorder)]
 
  for(i in 1:ncol(data.tmp2)) data.tmp2[,i]=as.numeric(as.character(data.tmp2[,i])) #convert each column to numeric
  cor.mat = cor(data.tmp2)
  
  for(i in 1:(ncol(cor.mat)-1)){
    excl.num = which(0.95< cor.mat[,i] & cor.mat[,i]<1 )
    excl = names(excl.num)
    data.tmp <- data.tmp[,!(names(data.tmp) %in% excl)]
    excl.mat = c(excl, colnames(cor.mat)[i])
    cor.mat <- cor.mat[!(rownames(cor.mat) %in% excl.mat),]
  }
  
  #discrete = c("urban_lvl", "region", "division", "Federal.Region.Code", "Census.Region.Code", "Hidden_AR1",'Hidden','Binary_AR1', "Binary")
  add <- c("Hidden_AR3", "Hidden_AR2","Hidden_AR1","Hidden","Binary_AR3","Binary_AR2","Binary_AR1","Binary")
  reorder <- match(c(discrete,add), names(data.tmp))
  reorder <- na.omit(reorder)
  for (i in reorder){
    data.tmp[,i] = as.factor(data.tmp[,i])
  }
  
  return(data.tmp)
}
    