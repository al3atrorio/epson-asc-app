#!/bin/sh

source /etc/update_key

echo " [update] Starting Update Process."

echo " [update] Decrypting the image"
openssl enc -aes-256-cbc -d -in /tmp/update_downloaded.swu -out /tmp/update_downloaded_decrypted.swu -K ${key} -iv ${iv} -S ${salt}
result=$?

echo " [update] Decryption result: $result"

if [ "${result}" != "0" ]; then
	echo " [update] ERROR - Update failed when decryption the image - Error Code: ${result}"
	exit 5
fi

partition=`fw_printenv current_partition | cut -f 2 -d "="`

echo " [update] Current partition is: ${partition}"

if [ $partition = "0" ]; then
	echo " [update] Updating Partition 1"
	
	swupdate -i /tmp/update_downloaded_decrypted.swu -e rootfs,bank1 -b "0 1 2 3 4 5 6 10" > /dev/null 2>&1
	result=$?
	
	echo " [update] Command result: $result"

	if [ "${result}" != "0" ]; then
		echo " [update] ERROR - Update Failed - Error Code: ${result}"
		exit 3
	fi
	
	echo " [update] Update Successful"
	exit 0
elif [ $partition = "1" ]; then
	echo " [update] Updating Partition 0"
	
	swupdate -i /tmp/update_downloaded_decrypted.swu -e rootfs,bank0 -b "0 1 2 3 7 8 9 10" > /dev/null 2>&1
	result=$?
	
	echo " [update] Command result: $result"

	if [ "${result}" != "0" ]; then
		echo " [update] ERROR - Update Failed - Error Code: ${result}"
		exit 3
	fi
	
	echo " [update] Update Successful"
	exit 0
else
    echo " [update] ERROR - Bug, invalid current partition!"
    exit 4
fi

exit 2
