### Unreleased
  - Add startup version log

### 2.0.0 2018-01-04
  - Add /info healthcheck endpoint
  - Add writing of response Json to downstream
  - Update Python version in procfile for CF
  - Remove reference to ftp server

### 1.6.0 2017-11-21
  - Changes for moving to cloudfoundry
  - Changed from using files in the os during transform and use memory instead

### 1.5.0 2017-11-01
  - Removed unchanging configurable variables.
  - Add all service configurations to config file
  - Begin using PyTest as default test runner
  - Rename FTP_HOST to FTP_PATH

### 1.4.0 2017-10-02
  - Update requirements to include hashes
  - Make use of image list endpoint
  - Update deleting tmp files
  - Remove pip from requirements and fix Docker build
  - Fix image file numbering
  - Add settings to image transformer

### 1.3.0 2017-07-25
  - Change all instances of ADD to COPY in Dockerfile

### 1.2.0 2017-07-10
  - Reformat image to make answers more prominent
  - Log `tx_id` for file creation
  - Add environment variables to README
  - Correct license attribution
  - Add codacy badge
  - Reworking reformat image to make it more readable
  - Add support for codecov to see unit test coverage

### 1.1.1 2017-03-17
  - Change env var read from `FTP_HOST` to `FTP_PATH`
  - Log image file paths

### 1.1.0 2017-03-15
  - Log version number on startup
  - Fix inverted constants in survey transform.
  - Change `status_code` to `status` for SDX logging
  - Change `calling service` and `returned from service` logging messages to add context

### 1.0.0 2017-02-16
  - Initial release
