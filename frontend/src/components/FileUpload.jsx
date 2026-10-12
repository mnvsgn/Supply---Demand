import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { validateFile, ALLOWED_EXTENSIONS } from '../utils/fileValidation';
import { formatFileSize } from '../utils/formatters';

/**
 * FileUpload provides drag-and-drop and click-to-upload functionality
 * with client-side file validation for CSV and XLSX files.
 */
export default function FileUpload({
  onFileSelect,
  isUploading = false,
  disabled = false,
  accept = '.csv,.xlsx',
  className = '',
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const [selectedFileName, setSelectedFileName] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    if (disabled || isUploading) return;
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled || isUploading) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
      e.target.value = '';
    }
  };

  const processFile = (file) => {
    const { isValid, error } = validateFile(file);
    if (!isValid) {
      setValidationError(error);
      return;
    }

    setValidationError(null);
    setSelectedFileName(file.name);
    if (onFileSelect) {
      onFileSelect(file);
    }
  };

  return (
    <div className={`w-full ${className}`}>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleInputChange}
        disabled={disabled || isUploading}
        className="hidden"
        aria-label="Upload dataset file"
      />

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-emerald-500 bg-emerald-950/20'
            : disabled
            ? 'border-[#262626] bg-[#141414] opacity-50 cursor-not-allowed'
            : 'border-[#2a2a2a] bg-[#161616] hover:border-[#383838] hover:bg-[#1a1a1a]'
        }`}
      >
        <div className="flex flex-col items-center justify-center space-y-2">
          {isUploading ? (
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-[#222222] text-neutral-400 flex items-center justify-center">
              <UploadCloud className="w-5 h-5 text-neutral-300" />
            </div>
          )}

          <div className="text-xs">
            <span className="font-medium text-neutral-200">
              {isUploading ? 'Uploading and validating...' : 'Click to upload or drag and drop'}
            </span>
            <p className="text-[11px] text-neutral-500 mt-0.5">
              CSV or XLSX spreadsheet (Max 50 MB)
            </p>
          </div>

          {selectedFileName && !isUploading && !validationError && (
            <div className="flex items-center space-x-1.5 text-xs text-emerald-400 pt-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span className="truncate max-w-[240px] font-mono">{selectedFileName}</span>
            </div>
          )}
        </div>
      </div>

      {validationError && (
        <div className="mt-2 flex items-center space-x-1.5 text-xs text-rose-400 bg-rose-950/30 border border-rose-900/40 rounded-lg p-2.5">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{validationError}</span>
        </div>
      )}
    </div>
  );
}
