package com.aptdemo.yzhao.androiddemo;

import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.support.v7.app.ActionBarActivity;
import android.util.Base64;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.Window;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.Toast;

import com.loopj.android.http.AsyncHttpClient;
import com.loopj.android.http.AsyncHttpResponseHandler;
import com.loopj.android.http.RequestParams;
import com.squareup.picasso.Picasso;

import org.apache.http.Header;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.util.ArrayList;

//import android.support.v7.app.AppCompatActivity;

public class RememberThis extends ActionBarActivity {
    static double mLatitude = 0.0;
    static double mLongitude = 0.0;
    static boolean took_photo = false;

    Context context = this;
    private String TAG  = "Remember This";
    private static final int CAMERA_IMAGE = 2;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_remember_this);
    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.display_images, menu);
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

    public void useMap(View view){
        Intent intent= new Intent(this, UseMap.class);
        intent.putExtra("Lat",mLatitude);
        intent.putExtra("Lon",mLongitude);
        startActivity(intent);
    }

    public void streetView(View view){

    }

    public void usePicture(View view){
        Intent intent= new Intent(this, CameraCapture.class);
        startActivityForResult(intent, CAMERA_IMAGE);
    }
    static byte[] b = null;
    public void viewPicture(View view){
        if(b != null) {
            Dialog imageDialog = new Dialog(context);
            imageDialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
            imageDialog.setContentView(R.layout.thumbnail);
            ImageView image = (ImageView) imageDialog.findViewById(R.id.thumbnail_IMAGEVIEW);

            Bitmap bitmap = BitmapFactory.decodeByteArray(b, 0, b.length);
            image.setImageBitmap(bitmap);

            imageDialog.show();
        }
    }


    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if(took_photo) {
            Matrix matrix = new Matrix();
            matrix.postRotate(90);

            String imageFilePath = data.getStringExtra("latestImageFileName");

            Bitmap bitmapImage = BitmapFactory.decodeFile(imageFilePath);
            final Bitmap rotatedBitmapImage = Bitmap.createBitmap(bitmapImage, 0, 0, bitmapImage.getWidth
                    (), bitmapImage.getHeight(), matrix, true);

            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            rotatedBitmapImage.compress(Bitmap.CompressFormat.JPEG, 50, baos);
            b = baos.toByteArray();
            byte[] encodedImage = Base64.encode(b, Base64.DEFAULT);
            String encodedImageStr = encodedImage.toString();
            took_photo = false;
        }
    }

    public void confirm(View view){
        String photoCaption = "";
        System.out.println("confirming");
        getUploadURL(b, photoCaption);
        b = null;
    }

    private void getUploadURL(final byte[] encodedImage, final String photoCaption){
        if(Homepage.email != null) {
            postToServer(encodedImage, photoCaption);
        }
    }

    private void postToServer(byte[] encodedImage,String photoCaption){

        String upload_url = "http://ParkingRightHere.appspot.com/park";
        System.out.println(upload_url);
        RequestParams params = new RequestParams();

        params.put("user_email", Homepage.email);
        if(encodedImage != null) {
            params.put("image", new ByteArrayInputStream(encodedImage));
        }
        params.put("lat", mLatitude);
        params.put("lon", mLongitude);
        params.put("description", photoCaption);

        AsyncHttpClient client = new AsyncHttpClient();
        client.post(upload_url, params, new AsyncHttpResponseHandler() {
            @Override
            public void onSuccess(int statusCode, Header[] headers, byte[] response) {
                Log.w("async", "success!!!!");
                Toast.makeText(context, "Parking Location Remebered!", Toast.LENGTH_SHORT).show();
            }

            @Override
            public void onFailure(int statusCode, Header[] headers, byte[] errorResponse, Throwable e) {
                Log.e("Posting_to_blob", "There was a problem in retrieving the url : " + e.toString
                        ());
            }
        });
    }
}
