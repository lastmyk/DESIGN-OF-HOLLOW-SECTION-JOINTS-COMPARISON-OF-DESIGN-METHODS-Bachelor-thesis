CREATE TABLE `idea_res` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `code_standard` varchar(100) DEFAULT NULL,
  `conn_type` text,
  `capacity` float DEFAULT NULL,
  `angle` float DEFAULT NULL,
  `steel_grade` int DEFAULT NULL,
  `nrd_direction` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `time_of_calc` timestamp NULL DEFAULT NULL,
  `specification` text,
  `m_perc` int DEFAULT NULL,
  `n_perc` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=86968 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;