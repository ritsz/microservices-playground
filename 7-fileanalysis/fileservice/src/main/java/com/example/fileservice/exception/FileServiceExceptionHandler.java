package com.example.fileservice.exception;

import java.time.LocalDateTime;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;

import com.example.fileservice.model.ErrorResponse;

import lombok.extern.slf4j.Slf4j;

@ControllerAdvice
@Slf4j
public class FileServiceExceptionHandler {
    /**
     * Handles the WorkloadPlatformServiceException exception.
     */
    @ExceptionHandler(FileServiceException.class)
    public ResponseEntity<ErrorResponse> handleCustomException(FileServiceException ex,
                                                               WebRequest request) {
        log.error(ex.getMessage(), ex);
        ErrorResponse error = new ErrorResponse();
        error.setTimestamp(LocalDateTime.now().toString());
        error.setError(ex.getStatus().getReasonPhrase());
        error.setMessage(ex.getMessage());
        error.setStatus(ex.getStatus().value());
        error.setPath(((ServletWebRequest) request).getRequest().getRequestURI());
        return new ResponseEntity<>(error, ex.getStatus());
    }

    /**
     * Handles the NotFound exception.
     */
    @ExceptionHandler(HttpClientErrorException.NotFound.class)
    public ResponseEntity<ErrorResponse> handleNotFound(HttpClientErrorException.NotFound ex, WebRequest request) {
        log.error(ex.getMessage(), ex);
        ErrorResponse error = new ErrorResponse();
        error.setTimestamp(LocalDateTime.now().toString());
        error.setError(ex.getMessage());
        error.setMessage(ex.getMessage());
        error.setStatus(ex.getStatusCode().value());
        error.setPath(((ServletWebRequest) request).getRequest().getRequestURI());
        return new ResponseEntity<>(error, ex.getStatusCode());
    }

    /**
     * Handles the MethodArgumentNotValidException exception.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationError(MethodArgumentNotValidException ex, WebRequest request) {
        log.error(ex.getMessage(), ex);
        ErrorResponse error = new ErrorResponse();
        error.setTimestamp(LocalDateTime.now().toString());
        error.setError(ex.getMessage());
        error.setMessage(ex.getMessage());
        error.setStatus(HttpStatus.BAD_REQUEST.value());
        error.setPath(((ServletWebRequest) request).getRequest().getRequestURI());
        return new ResponseEntity<>(error, HttpStatus.BAD_REQUEST);
    }
}
