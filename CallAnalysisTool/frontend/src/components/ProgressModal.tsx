"use client";
import React from "react";
import styles from "./ProgressModal.module.css";

interface ProgressModalProps {
  isOpen: boolean;
  progress: number; // 0-100
  currentStep: string;
}

const ProgressModal: React.FC<ProgressModalProps> = ({
  isOpen,
  progress,
  currentStep,
}) => {
  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <h2 className={styles.modalTitle}>Processing Files</h2>
        <div className={styles.progressContainer}>
          <div className={styles.progressBarWrapper}>
            <div
              className={styles.progressBar}
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className={styles.progressText}>{progress}%</p>
        </div>
        <p className={styles.currentStep}>{currentStep}</p>
      </div>
    </div>
  );
};

export default ProgressModal;
