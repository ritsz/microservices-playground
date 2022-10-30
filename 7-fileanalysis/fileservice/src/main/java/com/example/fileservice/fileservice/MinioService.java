package com.example.fileservice.fileservice;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.fileservice.configuration.MinioConfiguration;
import com.example.fileservice.exception.FileServiceException;

import io.minio.BucketExistsArgs;
import io.minio.DownloadObjectArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.ObjectWriteResponse;
import io.minio.UploadObjectArgs;
import io.minio.errors.MinioException;
import lombok.extern.slf4j.Slf4j;

@Service
@Slf4j
public class MinioService {

    String bucketName;

    MinioConfiguration configuration;

    @Autowired
    public MinioService(MinioConfiguration minioConfiguration) {
        bucketName = minioConfiguration.getBucketname();
        configuration = minioConfiguration;
    }

    public ObjectWriteResponse uploadFile(String name, byte[] content) {
        MinioClient minioClient = minioClient();

        log.info("Creating a bucket");
        createBucket(minioClient, this.bucketName);

        File file = new File("/tmp/" + name);
        file.canWrite();
        file.canRead();
        try {
            FileOutputStream iofs = new FileOutputStream(file);
            iofs.write(content);
            ObjectWriteResponse response = minioClient.uploadObject(
                UploadObjectArgs.builder()
                    .bucket(this.bucketName)
                    .object(file.getName())
                    .filename(file.getAbsolutePath())
                    .build());
            log.info("Response: {}", response);
            file.delete();
            return response;
        } catch (Exception ex) {
            log.error("Could not upload file: {}", name);
            throw new FileServiceException(ex.getLocalizedMessage());
        }
    }

    public File downloadFile(String originalFileName, String savedFileName) {
        File file = new File("/tmp/" + originalFileName);
        file.canWrite();
        file.canRead();
        if (file.exists()) {
            log.info("Deleting {}", file.getAbsolutePath());
            file.delete();
        }
        try {
            MinioClient minioClient = minioClient();
            minioClient.downloadObject(
                DownloadObjectArgs.builder()
                    .bucket(this.bucketName)
                    .object(savedFileName)
                    .filename(file.getAbsolutePath())
                    .build());
            return file;
        } catch (Exception ex) {
            log.error("Cannot download file: {}", savedFileName, ex);
            throw new FileServiceException(ex.getLocalizedMessage());
        }
    }

    private void createBucket(MinioClient minioClient, String bucketName) {
        try {
            boolean found = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
            if (!found) {
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
            } else {
                log.info("Bucket {} already exists.", bucketName);
            }
        } catch (MinioException | InvalidKeyException | IOException | NoSuchAlgorithmException e) {
            log.error("Could not create bucket: {}", bucketName, e);
            throw new FileServiceException(e.getLocalizedMessage());
        }
    }

    private MinioClient minioClient() {
        return MinioClient.builder()
            .endpoint(configuration.getEndpoint(), configuration.getPort(), configuration.getSkiptls())
            .credentials(configuration.getUsername(), configuration.getPassword())
            .build();
    }

}
