#!/bin/bash

# Define the current date
current_date=$(date +%Y-%m-%d)

# Backup the database and compress the backup file
backup_mongo() {
  ssh -i /path/server-a.pem root@ip-server-a << EOF
    docker exec mongo bash -c "mkdir -p /data/backup"
    mongodump --db fastgpt -u "myusername" -p "mypassword" --authenticationDatabase admin --out /data/backup
    tar -czvf /data/fastgpt-mongo-backup-${current_date}.tar.gz -C /data/backup .
  EOF
}

# Upload the backup file to server B and extract it
upload_and_restore() {
  rsync -avz --progress -e "ssh -i /path/server-b.pem" root@ip-server-a:/usr/fastgpt/mongobackup/fastgpt-mongo-backup-${current_date}.tar.gz /usr/fastgpt/mongobackup/
  watch -n 1 'du -h /usr/fastgpt/mongobackup/fastgpt-mongo-backup-${current_date}.tar.gz'
}

# Check if the backup or restore was successful and provide error information
check_result() {
  ssh -i /path/server-b.pem root@ip-server-b << EOF
    if [ -f /usr/fastgpt/mongobackup/fastgpt-mongo-backup-${current_date}.tar.gz ]; then
      echo "Backup and Restore Success!"
    else
      error_code=$?
      error_message=$(bash -c "echo 'Error occurred during Backup or Restore'")
      error_line_number=10
      echo "Error Code: $error_code"
      echo "Error Message: $error_message"
      echo "Error Line Number: $error_line_number"
    fi
  EOF
}

# Log function to record all actions
log_action() {
  now=$(date +"%Y-%m-%d %H:%M:%S")
  action_name=$1
  result=$2
  echo "$now - $action_name: $result" >> /var/log/mongo_backup.log
}

# Execute the backup and restore process and check the result
if backup_mongo; then
  log_action "Backup Mongo Database" "Success"
fi

if upload_and_restore; then
  sleep 5s
  log_action "Upload and Restore Backup File" "Success"
fi

check_result

log_action "Check Result" $(check_result)