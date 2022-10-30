package com.example.fileservice.model;

import java.util.UUID;

import com.fasterxml.jackson.databind.PropertyNamingStrategy;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import lombok.Data;

@Data
@JsonNaming(PropertyNamingStrategy.SnakeCaseStrategy.class)
public class FileInfo {

    public enum UploadStatus {
        FAILED,
        INPROGRESS,
        DONE
    }

    UUID id;
    String fileName;
    String bucketName;
    String etag;
    String region;
    String versionId;
    Long firstUploadTime;
    Long lastUploadTime;
    String sha256;
    Long fileSize;
    UploadStatus uploadStatus;
}
