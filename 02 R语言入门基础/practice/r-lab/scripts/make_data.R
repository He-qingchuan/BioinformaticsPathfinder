# 原创模拟数据。运行位置：r-lab 项目根目录。只在显式调用时重建 data。
# 随机种子固定；这些数值不代表任何真实公园、材料或研究发现。
set.seed(20260917)
dir.create("data", showWarnings = FALSE)
write_data <- function(x, name) write.csv(x, file.path("data", name), row.names = FALSE, na = "", fileEncoding = "UTF-8")
sites <- data.frame(site_id = c("P01", "P02", "P03"), site_name = c("Riverside", "Meadow", "Grove"), canopy_pct = c(45, 12, 78))
write_data(sites, "sites.csv")
make_records <- function(days, prefix) {
 x <- expand.grid(site_id = sites$site_id, period = c("morning", "afternoon"), date = as.character(days), stringsAsFactors = FALSE)
 x$record_id <- sprintf("%s%03d", prefix, seq_len(nrow(x)))
 x$temperature_c <- round(30 + ifelse(x$period == "afternoon", 3, 0) - sites$canopy_pct[match(x$site_id, sites$site_id)] / 30 + rnorm(nrow(x), 0, 0.8), 1)
 x$visitors <- sample(8:60, nrow(x), replace = TRUE)
 x$note <- rep(c("  regular ", "regular", " CHECK "), length.out = nrow(x))
 x[, c("record_id", "site_id", "date", "period", "temperature_c", "visitors", "note")]
}
x <- make_records(as.Date("2026-06-01") + 0:6, "O")
x$temperature_c[c(5, 28)] <- NA_real_
x$date[17] <- gsub("-", "/", x$date[17])
write_data(rbind(x, x[7, ]), "observations.csv")
wide <- data.frame(site_id = sites$site_id, morning = c(27.8, 29.6, 26.9), afternoon = c(31.1, 33.0, 29.7))
write_data(wide, "temperatures_wide.csv")
# 独立装置随机分配 A/B 两种遮阳材料；每个装置只报告一次降温值。
trial <- data.frame(unit_id = sprintf("U%02d", 1:48), material = sample(rep(c("A", "B"), each = 24)))
trial$start_c <- round(rnorm(48, 35, 1.2), 2)
trial$drop_c <- round(ifelse(trial$material == "B", 3.4, 2.2) + rnorm(48, 0, 0.95), 2)
trial$end_c <- round(trial$start_c - trial$drop_c, 2)
write_data(trial, "shade_trial.csv")
# 模拟横断面资料：30 个独立地点，各观测一次，不是前三个地点的重复测量。
parks <- data.frame(site_id = sprintf("S%02d", 1:30), canopy_pct = round(runif(30, 10, 85), 1))
parks$temperature_c <- round(35 - 0.07 * parks$canopy_pct + rnorm(30, 0, 0.85), 2)
write_data(parks, "independent_sites.csv")
fresh <- make_records(as.Date("2026-06-08") + 0:1, "N")
fresh$temperature_c[4] <- NA_real_
write_data(rbind(fresh, fresh[2, ]), "new_observations.csv")
cat("已写入 6 份模拟数据；原始观察 43 行，新记录 13 行。\n")
