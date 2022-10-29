package com.example.fileservice.model;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import java.util.UUID;

import lombok.Builder;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

@Entity
@Getter
@Setter
@ToString
@EqualsAndHashCode
public class FileEntity {

    @Id
    @Column(name = "id", nullable = false)
    @GeneratedValue(strategy = GenerationType.AUTO)
    private UUID id;

    String fileName;
    String bucketName;
    String etag;
    String region;
    String versionId;
    Long firstUploadTime;
    Long lastUploadTime;
    String sha256;
    String uploadStatus;
    String status;
    Long fileSize;

    public FileEntity() {

    }
}
