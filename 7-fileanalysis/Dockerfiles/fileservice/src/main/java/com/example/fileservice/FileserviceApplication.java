package com.example.fileservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
//import org.springframework.metrics.export.prometheus.EnablePrometheusMetrics;

@SpringBootApplication
//@EnablePrometheusMetrics
public class FileserviceApplication {

    public static void main(String[] args) {
        SpringApplication.run(FileserviceApplication.class, args);
    }

}
