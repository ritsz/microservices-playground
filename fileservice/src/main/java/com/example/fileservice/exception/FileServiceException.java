package com.example.fileservice.exception;

import org.springframework.http.HttpStatus;

import lombok.Getter;

public class FileServiceException extends RuntimeException {

    @Getter
    private final HttpStatus status;

    public FileServiceException(String message) {
        super(message);
        this.status = HttpStatus.INTERNAL_SERVER_ERROR;
    }

    public FileServiceException(String message, HttpStatus status) {
        super(message);
        this.status = status;
    }

}
