# Uploading Files to Microsoft Azure via Notecard and Notehub

## Microsoft Azure Setup

1. **Create a Microsoft Azure Account**
   - If you haven’t done so already, create a Microsoft Azure account at [azure.microsoft.com](https://azure.microsoft.com). Note that you will need to provide a phone number for verification and credit or debit card details for authorization. You won’t be charged for the initial free period unless you switch to pay-as-you-go pricing.

2. **Create a Storage Account**
   - Once logged into your Azure account, navigate to **Storage accounts**.

     <img src="azure_images/azure_storage_accounts.png" style="border: 1px solid lightgray;">

   - If you don’t have a storage account yet, click **+Create**.
   - Choose a name for your Storage account. Leave all other options at their default values.

     <img src="azure_images/azure_create_storage_account.png" style="border: 1px solid lightgray;">

   - Click **Review + create** and then **Create**.

3. **Access Your Storage Account**
   - After the resources are created, click **Go to resource** on the deployment complete screen.

4. **Create a Container**
   - Navigate to **Data storage** → **Containers**.
   - Click the **+ Container** button to create a new container.
   - Name your container (e.g., `bluesfilescontainer`).

5. **Generate SAS Key**
   - Once the container is created, click the three dots (…) next to your container.

     <img src="azure_images/azure_generate_sas_key_1.png" style="border: 1px solid lightgray;">

   - Click **Generate SAS**.
   - Select the following permissions:
     - Read
     - Add
     - Create
     - Write
     - Delete
   - The SAS key will have a default expiry time. Optionally, extend this duration for testing to avoid authentication issues.
   - Click **Generate SAS token and URL** to generate the key.
   - Copy the **Blob SAS URL** for use in the next steps.

     <img src="azure_images/azure_generate_sas_key_2.png" style="border: 1px solid lightgray;">


6. **Test Azure Container Setup**
   - Copy the generated SAS URL from the previous step.
   - Add the name you want your file to be saved as in Azure. For example, if you want to save your file as 'datafile', modify the URL by adding a forward slash "/" after the storage container name, followed by the desired file name. For example, before modifying, the URL looks like this:-

     `
     https://ysazurestorage.blob.core.windows.net/bluesfilescontainer?sp=racw&st=2024-08-01T11:15:56Z&se=2024-08-01T19:15:56Z&spr=https&sv=2022-11-02&sr=c&sig=Kzo3CL%2BkVm74PTdHM5OoxbjsdHyuc1c1KwDnfkcBjJg%3D
     `

     After the URL is modified, it should look like this

     `
     https://ysazurestorage.blob.core.windows.net/bluesfilescontainer`**`/datafile`**`?sp=racw&st=2024-08-01T11:15:56Z&se=2024-08-01T19:15:56Z&spr=https&sv=2022-11-02&sr=c&sig=Kzo3CL%2BkVm74PTdHM5OoxbjsdHyuc1c1KwDnfkcBjJg%3D
     `

     Note that the string "/datafile" was added after "bluesfilecontainer".

   - Finally, use the following `curl` command to verify that the Azure container is set up correctly and to test file uploads:

     ```bash
     curl -i -X PUT \
       -H "x-ms-blob-type: BlockBlob"
       --upload-file myfile.txt \
       <Generated_SAS_URL_plus_target_filename>
     ```


     Using the generated link and filename from the example above, the full curl request should look like this:-

     ```bash
     curl -i -X PUT \
       -H "x-ms-blob-type: BlockBlob"
       --upload-file myfile.txt \
       "https://iotcsayau4ueernijnm.blob.core.windows.net/test-container-20240719/myfile.txt?sp=r&st=2024-07-19T21:20:38Z&se=2024-07-20T05:20:38Z&spr=https&sv=2022-11-02&sr=c&sig=muUfzJZG1K635lTDft0yFyQm4ryQxFU9LsXH4XzrU28%3D"
     ```

     If the Azure storage container has been set up correctly, the curl request should succeed, and the string **Created** should appear in the response message. This can also be verified by checking that the file has been created in the Azure storage container account.

## Notehub Setup

1. **Navigate to Notehub**
   - Go to [notehub.io/projects](https://notehub.io/projects).

2. **Create or Access a Project**
   - Create a new Notehub project or select an existing one.

3. **Create a New Route**
   - Click **Routes** from the navigation menu on the left-hand side.
   - Click **Create Route** on the upper right.
   - Select **Web Proxy Route**.

4. **Configure the Route**
   - Set the following:
     - **Route name**: `azure_file_transfer`
     - **URL**: Use the URL copied from step 5 of the Azure setup.
     - **Alias**: `ping`

5. **Add HTTP Headers**
   - Select **Additional Headers** and add the following header:
     - `x-ms-blob-type: BlockBlob`

6. **Specify the Destination Path**
   - Add a forward slash `/` followed by `[$filename]` before the first "?" as can be seen in the image below. This is needed so that the source filename is copied to Azure.

     <img src="azure_images/azure_notehub_setup_filename.png" style="border: 1px solid lightgray;">


7. **Create the Route**
   - Click **Create Route**.

## Notecard Setup

Once Azure and Notehub have been configured correctly, you can launch the Python script with the following command:

```bash
python main.py -B 100000 -w put -i -s "azure" -u <notehub_product_uid> -f <path_to_file_to_send>
```

**Example:**

```bash
python main.py -B 100000 -w put -i -s "azure" -u com.blues.large_file_transfer -f image.png -p /dev/tty.usbmodemNOTE1
```
