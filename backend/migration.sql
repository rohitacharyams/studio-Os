-- Add new columns to dance_classes table
ALTER TABLE dance_classes ADD images NVARCHAR(MAX) NULL;
ALTER TABLE dance_classes ADD videos NVARCHAR(MAX) NULL;
ALTER TABLE dance_classes ADD artist_details NVARCHAR(MAX) NULL;
ALTER TABLE dance_classes ADD what_to_bring NVARCHAR(MAX) NULL;
ALTER TABLE dance_classes ADD prerequisites NVARCHAR(MAX) NULL;
ALTER TABLE dance_classes ADD tags NVARCHAR(MAX) NULL;

-- Add new columns to studios table
ALTER TABLE studios ADD photos NVARCHAR(MAX) NULL;
ALTER TABLE studios ADD videos NVARCHAR(MAX) NULL;
ALTER TABLE studios ADD testimonials NVARCHAR(MAX) NULL;
ALTER TABLE studios ADD about NVARCHAR(MAX) NULL;
ALTER TABLE studios ADD amenities NVARCHAR(MAX) NULL;
ALTER TABLE studios ADD social_links NVARCHAR(MAX) NULL;
