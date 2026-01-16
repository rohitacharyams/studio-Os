-- Azure SQL Server Migration Script
-- Run these statements on studioos_db database
-- Applies migrations 003, 004, 005, and 006

-- Migration 003: Add theme_settings to studios table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'studios' AND COLUMN_NAME = 'theme_settings')
    ALTER TABLE studios ADD theme_settings NVARCHAR(MAX);
GO

-- Migration 004: Add media fields to studios table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'studios' AND COLUMN_NAME = 'photos')
    ALTER TABLE studios ADD photos NVARCHAR(MAX);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'studios' AND COLUMN_NAME = 'videos')
    ALTER TABLE studios ADD videos NVARCHAR(MAX);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'studios' AND COLUMN_NAME = 'testimonials')
    ALTER TABLE studios ADD testimonials NVARCHAR(MAX);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'studios' AND COLUMN_NAME = 'amenities')
    ALTER TABLE studios ADD amenities NVARCHAR(MAX);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'studios' AND COLUMN_NAME = 'social_links')
    ALTER TABLE studios ADD social_links NVARCHAR(MAX);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'studios' AND COLUMN_NAME = 'about')
    ALTER TABLE studios ADD about NVARCHAR(MAX);
GO

-- Migration 005: Add instructor fields to dance_classes and class_sessions
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'dance_classes' AND COLUMN_NAME = 'instructor_name')
    ALTER TABLE dance_classes ADD instructor_name NVARCHAR(255);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'dance_classes' AND COLUMN_NAME = 'instructor_description')
    ALTER TABLE dance_classes ADD instructor_description NVARCHAR(MAX);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'dance_classes' AND COLUMN_NAME = 'instructor_instagram_handle')
    ALTER TABLE dance_classes ADD instructor_instagram_handle NVARCHAR(100);
GO

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'class_sessions' AND COLUMN_NAME = 'instructor_name')
    ALTER TABLE class_sessions ADD instructor_name NVARCHAR(255);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'class_sessions' AND COLUMN_NAME = 'substitute_instructor_name')
    ALTER TABLE class_sessions ADD substitute_instructor_name NVARCHAR(255);
GO

-- Migration 006: Add Razorpay fields to bookings table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'bookings' AND COLUMN_NAME = 'razorpay_payment_id')
    ALTER TABLE bookings ADD razorpay_payment_id NVARCHAR(100);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'bookings' AND COLUMN_NAME = 'razorpay_order_id')
    ALTER TABLE bookings ADD razorpay_order_id NVARCHAR(100);
GO

-- Migration 007: Add QR code and attendance fields to bookings table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'bookings' AND COLUMN_NAME = 'qr_code_token')
    ALTER TABLE bookings ADD qr_code_token NVARCHAR(100);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'bookings' AND COLUMN_NAME = 'qr_code_url')
    ALTER TABLE bookings ADD qr_code_url NVARCHAR(500);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'bookings' AND COLUMN_NAME = 'pdf_url')
    ALTER TABLE bookings ADD pdf_url NVARCHAR(500);
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'bookings' AND COLUMN_NAME = 'attendance_marked_at')
    ALTER TABLE bookings ADD attendance_marked_at DATETIME;
GO

-- Add unique constraint to qr_code_token (must check for existing constraint first)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID('bookings') AND name = 'UQ_bookings_qr_code_token')
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UQ_bookings_qr_code_token ON bookings(qr_code_token) WHERE qr_code_token IS NOT NULL;
END
GO

PRINT 'Migrations applied successfully!';
