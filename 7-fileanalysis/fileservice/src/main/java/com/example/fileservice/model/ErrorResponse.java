package com.example.fileservice.model;

import java.io.Serializable;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

@Data
public class ErrorResponse implements Serializable {
    @JsonProperty("timestamp")
    private String timestamp = null;

    @JsonProperty("status")
    private Integer status = null;

    @JsonProperty("error")
    private String error = null;

    @JsonProperty("message")
    private String message = null;

    @JsonProperty("path")
    private String path = null;
}
