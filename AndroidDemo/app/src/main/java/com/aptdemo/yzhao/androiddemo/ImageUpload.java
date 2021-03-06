package com.aptdemo.yzhao.androiddemo;

import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.location.Location;
import android.net.Uri;
import android.provider.MediaStore;
import android.support.v7.app.ActionBarActivity;
import android.os.Bundle;
import android.util.Base64;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.api.GoogleApiClient;
import com.google.android.gms.common.api.GoogleApiClient.OnConnectionFailedListener;
import com.google.android.gms.location.LocationServices;

import com.loopj.android.http.AsyncHttpClient;
import com.loopj.android.http.AsyncHttpResponseHandler;
import com.loopj.android.http.RequestParams;

import org.apache.http.Header;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;


public class ImageUpload extends ActionBarActivity implements GoogleApiClient.ConnectionCallbacks ,OnConnectionFailedListener {
    private static final int PICK_IMAGE = 1;
    private static final int CAMERA_IMAGE = 2;
    private String curStream = "";
    Context context = this;

    protected GoogleApiClient mGoogleApiClient;
    protected Location mLastLocation;
    protected double mLatitude;
    protected double mLongitude;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_image_upload);

        curStream = DisplayStreamImages.STREAM;


        TextView tv = (TextView) findViewById(R.id.cur_stream);
        tv.setText("Stream: " + curStream);

        // Choose image from library
        Button chooseFromLibraryButton = (Button) findViewById(R.id.choose_from_library);
        chooseFromLibraryButton.setOnClickListener(
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {

                        // To do this, go to AndroidManifest.xml to add permission
                        Intent galleryIntent = new Intent(Intent.ACTION_PICK,
                                android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
                        // Start the Intent
                        startActivityForResult(galleryIntent, PICK_IMAGE);
                    }
                }
        );

        buildGoogleApiClient();
    }

    protected synchronized void buildGoogleApiClient() {
        mGoogleApiClient = new GoogleApiClient.Builder(this)
                .addConnectionCallbacks(this)
                .addOnConnectionFailedListener(this)
                .addApi(LocationServices.API)
                .build();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.image_upload, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();
        if (id == R.id.action_settings) {
            return true;
        }
        return super.onOptionsItemSelected(item);
    }


    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_IMAGE && data != null && data.getData() != null) {
            Uri selectedImage = data.getData();

            // User had pick an image.

            String[] filePathColumn = {MediaStore.Images.ImageColumns.DATA};
            Cursor cursor = getContentResolver().query(selectedImage, filePathColumn, null, null, null);
            cursor.moveToFirst();

            // Link to the image

            int columnIndex = cursor.getColumnIndex(filePathColumn[0]);
            String imageFilePath = cursor.getString(columnIndex);
            cursor.close();

            // Bitmap imaged created and show thumbnail

            ImageView imgView = (ImageView) findViewById(R.id.thumbnail);
            final Bitmap bitmapImage = BitmapFactory.decodeFile(imageFilePath);
            imgView.setImageBitmap(bitmapImage);

            // Enable the upload button once image has been uploaded

            Button uploadButton = (Button) findViewById(R.id.upload_to_server);
            uploadButton.setClickable(true);

            uploadButton.setOnClickListener(
                    new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {

                            // Get photo caption

                            EditText text = (EditText) findViewById(R.id.upload_message);
                            String photoCaption = text.getText().toString();

                            ByteArrayOutputStream baos = new ByteArrayOutputStream();
                            bitmapImage.compress(Bitmap.CompressFormat.JPEG, 50, baos);
                            byte[] b = baos.toByteArray();
                            byte[] encodedImage = Base64.encode(b, Base64.DEFAULT);
                            String encodedImageStr = encodedImage.toString();

                            getUploadURL(b, photoCaption);
                        }
                    }
            );
        }
        else if(requestCode == CAMERA_IMAGE){

            Button uploadButton = (Button) findViewById(R.id.upload_to_server);
            uploadButton.setClickable(true);

            Matrix matrix = new Matrix();
            matrix.postRotate(90);

            String imageFilePath = data.getStringExtra("latestImageFileName");
            Bitmap bitmapImage = BitmapFactory.decodeFile(imageFilePath);
            final Bitmap rotatedBitmapImage = Bitmap.createBitmap(bitmapImage, 0, 0, bitmapImage.getWidth(), bitmapImage.getHeight(), matrix, true);

            ImageView imgView = (ImageView) findViewById(R.id.thumbnail);
            imgView.setImageBitmap(rotatedBitmapImage);

            Toast.makeText(context, "Check the preview and press Upload below!", Toast.LENGTH_SHORT).show();

            uploadButton.setOnClickListener(
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                    // Get photo caption

                    EditText text = (EditText) findViewById(R.id.upload_message);
                    String photoCaption = text.getText().toString();

                    ByteArrayOutputStream baos = new ByteArrayOutputStream();
                    rotatedBitmapImage.compress(Bitmap.CompressFormat.JPEG, 50, baos);
                    byte[] b = baos.toByteArray();
                    byte[] encodedImage = Base64.encode(b, Base64.DEFAULT);
                    String encodedImageStr = encodedImage.toString();

                    getUploadURL(b, photoCaption);
                    }
                }
            );

        }
    }

    private void getUploadURL(final byte[] encodedImage, final String photoCaption){
        AsyncHttpClient httpClient = new AsyncHttpClient();
//        String request_url="http://aptandroiddemo.appspot.com/getUploadURL";
        String request_url="http://phase3back.appspot.com/getUploadURL";
        System.out.println(request_url);
        httpClient.get(request_url, new AsyncHttpResponseHandler() {
            String upload_url;

            @Override
            public void onSuccess(int statusCode, Header[] headers, byte[] response) {

                try {
                    JSONObject jObject = new JSONObject(new String(response));

                    upload_url = jObject.getString("upload_url");
                    postToServer(encodedImage, photoCaption, upload_url);

                } catch (JSONException j) {
                    System.out.println("JSON Error");
                }
            }

            @Override
            public void onFailure(int statusCode, Header[] headers, byte[] errorResponse, Throwable e) {
                Log.e("Get_serving_url", "There was a problem in retrieving the url : " + e.toString());
            }
        });
    }

    private void postToServer(byte[] encodedImage,String photoCaption, String upload_url){

        upload_url = "http://connexus0.appspot.com/android";
        System.out.println(upload_url);
        RequestParams params = new RequestParams();
        //params.put("file",new ByteArrayInputStream(encodedImage));
        //params.put("photoCaption", photoCaption);

        params.put("stream", curStream);
        params.put("file",new ByteArrayInputStream(encodedImage));
        params.put("lat", mLatitude);
        params.put("lon", mLongitude);
        params.put("caption", photoCaption);

        AsyncHttpClient client = new AsyncHttpClient();
        client.post(upload_url, params, new AsyncHttpResponseHandler() {
            @Override
            public void onSuccess(int statusCode, Header[] headers, byte[] response) {
                Log.w("async", "success!!!!");
                Toast.makeText(context, "Upload Successful", Toast.LENGTH_SHORT).show();
            }

            @Override
            public void onFailure(int statusCode, Header[] headers, byte[] errorResponse, Throwable e) {
                Log.e("Posting_to_blob", "There was a problem in retrieving the url : " + e.toString());
            }
        });
    }

    public void viewAllImages(View view){
        Intent intent= new Intent(this, DisplayImages.class);
        startActivity(intent);
    }

    public void useCameraCapture(View view){
        Intent intent= new Intent(this, CameraCapture.class);
        startActivityForResult(intent, CAMERA_IMAGE);
    }

    @Override
    protected void onStart() {
        super.onStart();
        mGoogleApiClient.connect();
    }

    @Override
    protected void onStop() {
        super.onStop();
        if (mGoogleApiClient.isConnected()) {
            mGoogleApiClient.disconnect();
        }
    }

    @Override
    public void onConnected(Bundle bundle) {
        mLastLocation = LocationServices.FusedLocationApi.getLastLocation(mGoogleApiClient);
        if (mLastLocation != null) {
            mLatitude = mLastLocation.getLatitude();
            mLongitude = mLastLocation.getLongitude();
            System.out.println(mLatitude);
            System.out.println(mLongitude);
        }
    }

    @Override
    public void onConnectionFailed(ConnectionResult connectionResult) {

    }

    @Override
    public void onConnectionSuspended(int i) {
        mGoogleApiClient.connect();
    }
}
