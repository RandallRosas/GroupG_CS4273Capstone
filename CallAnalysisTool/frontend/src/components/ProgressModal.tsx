"use client";
import React from "react";
import styles from "./ProgressModal.module.css";

interface ProgressModalProps {
  title: string;
  oneFile: boolean;
  isOpen: boolean;
  progress: number; // 0-100
  currentStep: string;
  elapsedTime?: string;
  currentFileElapsedTime?: string;
  showProgressBar?: boolean;
}

const ProgressModal: React.FC<ProgressModalProps> = ({
  title,
  oneFile,
  isOpen,
  progress,
  currentStep,
  elapsedTime,
  currentFileElapsedTime,
  showProgressBar = true,
}) => {
  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <h2 className={styles.modalTitle}>{title}</h2>
        {showProgressBar && (
          <div className={styles.progressContainer}>
            <div className={styles.progressBarWrapper}>
              <div
                className={styles.progressBar}
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className={styles.progressText}>{progress}%</p>
          </div>
        )}
        <p className={styles.currentStep}>{currentStep}</p>
        {!oneFile && (
          <p className={styles.currentStep}>
            Time Elapsed (Current File): {elapsedTime} ({currentFileElapsedTime})
          </p>
        )}
        {oneFile && (
          <p className={styles.currentStep}>
            Time Elapsed: {elapsedTime}
          </p>
        )}
      </div>
    </div>
  );
};

export default ProgressModal;
