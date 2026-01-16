-- Migration 007: Add QR code and attendance tracking fields to bookings table

-- Add QR code token (unique verification token for QR code)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('bookings') AND name = 'qr_code_token')
BEGIN
    ALTER TABLE bookings ADD qr_code_token VARCHAR(100) NULL;
    PRINT 'Added qr_code_token column to bookings table';
END
ELSE
BEGIN
    PRINT 'qr_code_token column already exists in bookings table';
END
GO

-- Add unique constraint to qr_code_token
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID('bookings') AND name = 'UQ_bookings_qr_code_token')
BEGIN
    ALTER TABLE bookings ADD CONSTRAINT UQ_bookings_qr_code_token UNIQUE (qr_code_token);
    PRINT 'Added unique constraint to qr_code_token';
END
ELSE
BEGIN
    PRINT 'Unique constraint on qr_code_token already exists';
END
GO

-- Add QR code image URL (S3 URL for QR code PNG)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('bookings') AND name = 'qr_code_url')
BEGIN
    ALTER TABLE bookings ADD qr_code_url VARCHAR(500) NULL;
    PRINT 'Added qr_code_url column to bookings table';
END
ELSE
BEGIN
    PRINT 'qr_code_url column already exists in bookings table';
END
GO

-- Add PDF URL (S3 URL for booking confirmation PDF with QR code)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('bookings') AND name = 'pdf_url')
BEGIN
    ALTER TABLE bookings ADD pdf_url VARCHAR(500) NULL;
    PRINT 'Added pdf_url column to bookings table';
END
ELSE
BEGIN
    PRINT 'pdf_url column already exists in bookings table';
END
GO

-- Add attendance marked timestamp
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('bookings') AND name = 'attendance_marked_at')
BEGIN
    ALTER TABLE bookings ADD attendance_marked_at DATETIME NULL;
    PRINT 'Added attendance_marked_at column to bookings table';
END
ELSE
BEGIN
    PRINT 'attendance_marked_at column already exists in bookings table';
END
GO

PRINT 'Migration 007 completed successfully';
