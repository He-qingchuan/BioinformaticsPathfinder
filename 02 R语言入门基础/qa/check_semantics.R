# Execute from an isolated copy of r-lab; supplied by qa/check_semantics.py.
suppressPackageStartupMessages(library(dplyr))
source("scripts/analyse.R")
x <- read.csv("data/observations.csv")
sites <- read.csv("data/sites.csv")
trial <- read.csv("data/shade_trial.csv")
parks <- read.csv("data/independent_sites.csv")
stopifnot(nrow(x) == 43L, nrow(distinct(x)) == 42L,
          sum(is.na(distinct(x)$temperature_c)) == 2L,
          !anyDuplicated(sites$site_id), !anyDuplicated(trial$unit_id),
          !anyDuplicated(parks$site_id), nrow(parks) == 30L)
stopifnot(max(abs(trial$start_c - trial$end_c - trial$drop_c)) < 1e-10,
          all(table(trial$material) == 24L))
# Check the Welch result against explicit mean, SE and Satterthwaite equations.
a <- trial$drop_c[trial$material == "A"]; b <- trial$drop_c[trial$material == "B"]
v_a <- var(a) / length(a); v_b <- var(b) / length(b)
se <- sqrt(v_a + v_b)
df <- (v_a + v_b)^2 / (v_a^2 / (length(a)-1) + v_b^2 / (length(b)-1))
difference <- mean(b)-mean(a)
expected_ci <- difference + c(-1, 1) * qt(.975, df) * se
expected_p <- 2 * pt(-abs(difference / se), df)
test <- t.test(b, a, var.equal = FALSE)
stopifnot(max(abs(unname(test$conf.int) - expected_ci)) < 1e-10,
          abs(test$p.value - expected_p) < 1e-12)
model <- lm(temperature_c ~ canopy_pct, data=parks)
manual_slope <- cov(parks$canopy_pct, parks$temperature_c)/var(parks$canopy_pct)
stopifnot(abs(coef(model)[[2]] - manual_slope) < 1e-12,
          max(abs(residuals(model) - (parks$temperature_c-fitted(model)))) < 1e-10)
# Full result: conservation of records and missing counts, not just file existence.
result <- analyse_records("data/observations.csv", "results/semantic-first")
stopifnot(identical(unname(result$audit), c(43L, 1L, 42L, 2L)),
          sum(result$summary$n_valid) == 40L,
          sum(result$summary$n_records) == 42L)
fresh <- analyse_records("data/new_observations.csv", "results/semantic-next")
stopifnot(identical(unname(fresh$audit), c(13L, 1L, 12L, 1L)),
          sum(fresh$summary$n_valid) == 11L)
# Relate report numbers to data and tests; the report must disclose separate designs.
report <- paste(readLines("results/semantic-first/report.md", encoding="UTF-8"), collapse="\n")
stopifnot(grepl(sprintf("%.3f", difference), report, fixed=TRUE),
          grepl(sprintf("%.3f", expected_ci[1]), report, fixed=TRUE),
          grepl("同一地点重复测量", report, fixed=TRUE),
          grepl("固定的实验与横断面", report, fixed=TRUE))
# Invalid input must fail with a useful reason, before an analysis is reported.
expect_failure <- function(data, reason) {
  file <- tempfile(fileext=".csv")
  write.csv(data, file, row.names=FALSE, na="")
  message <- tryCatch({analyse_records(file, "results/should-not-exist"); "NO ERROR"}, error=function(e) conditionMessage(e))
  stopifnot(grepl(reason, message, fixed=TRUE), !file.exists("results/should-not-exist/report.md"))
  unlink(file)
}
bad <- x; bad$temperature_c <- NULL; expect_failure(bad, "Missing required columns")
bad <- x; bad$record_id[2] <- bad$record_id[1]; expect_failure(bad, "Conflicting or missing record IDs")
bad <- x; bad$date[2] <- "not-a-date"; expect_failure(bad, "Invalid date")
bad <- x; bad$site_id[2] <- "UNKNOWN"; expect_failure(bad, "Unknown site ID")
bad <- x; bad$temperature_c[2] <- Inf; expect_failure(bad, "Non-finite temperature")
# A completely missing site's temperatures remain NA and n_valid=0, never zero degrees.
missing_group <- x; missing_group$temperature_c[missing_group$site_id == "P01"] <- NA_real_
write.csv(missing_group, "results/all-missing-group.csv", row.names=FALSE, na="")
m <- analyse_records("results/all-missing-group.csv", "results/missing-group")
stopifnot(is.na(m$summary$mean_c[m$summary$site_id=="P01"]),
          m$summary$n_valid[m$summary$site_id=="P01"] == 0L)
# Guard failed joins and malformed observational units independently of the report.
bad_sites <- rbind(sites, sites[1, ])
join_error <- tryCatch({left_join(x, bad_sites, by="site_id", relationship="many-to-one"); FALSE}, error=function(e) TRUE)
stopifnot(join_error)
cat("PASS: input accounting, Welch equations, OLS identity, report traceability, new data, 5 invalid-input cases, all-missing group, duplicate join keys.\n")
