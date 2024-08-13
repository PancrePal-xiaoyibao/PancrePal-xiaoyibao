#!/bin/bash

# Define the current date
current_date=$(date +%Y-%m-%d)

# Backup the database
echo "Starting database backup..."
ssh -i /path/server-a.pem root@ip-server-a << EOF
docker exec -it mongo mongodump --db fastgpt -u "myusername" -p "mypassword" --authenticationDatabase admin --out /data/backup
sleep 15
echo "Database backup completed."
EOF

# Compress the backup file
echo "Compressing backup file..."
docker exec mongo bash -c "tar -czvf /data/fastgpt-mongo-backup-${current_date}.tar.gz -C /data/backup ."
sleep 2
echo "Compression completed."

# Copy the compressed file to the server directory
echo "Copying compressed file to server directory..."
docker cp mongo:/data/fastgpt-mongo-backup-${current_date}.tar.gz /usr/fastgpt/mongobackup
sleep 1
echo "Copy completed."

# Clean up temporary files
echo "Cleaning up temporary files..."
docker exec mongo bash -c "rm -rf /data/backup/fastgpt"
sleep 1
echo "Cleanup completed."

# Upload the backup file to server B
echo "Uploading backup file to server B..."
rsync -avz --progress -e "ssh -i /path/server-b.pem" root@ip-server-a:/usr/fastgpt/mongobackup/fastgpt-mongo-backup-${current_date}.tar.gz root@ip-server-b:/usr/fastgpt/mongobackup/
sleep 5
echo "Upload completed."

# SSH to server B and restore the database
ssh -i /path/server-b.pem root@ip-server-b << EOF
echo "Extracting backup file..."
tar -xzvf /usr/fastgpt/mongobackup/fastgpt-mongo-backup-${current_date}.tar.gz -C /usr/fastgpt/mongobackup/
sleep 2
echo "Extraction completed."

echo "Preparing restore..."
docker exec mongo bash -c "mkdir -p /tmp/backup"
docker cp /usr/fastgpt/mongobackup/fastgpt-mongo-backup-${current_date}.tar.gz mongo:/tmp/backup
sleep 2
echo "Prepare restore completed."

echo "Restoring database..."
docker exec -it mongo mongorestore -u "myusername" -p "mypassword" --authenticationDatabase admin /tmp/backup --db fastgpt
sleep 15
echo "Restore completed."
EOF

echo "All operations completed."
