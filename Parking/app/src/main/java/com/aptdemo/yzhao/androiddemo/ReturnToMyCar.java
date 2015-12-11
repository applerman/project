package com.aptdemo.yzhao.androiddemo;

import android.app.Dialog;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.Window;
import android.widget.AdapterView;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.Toast;

import com.loopj.android.http.AsyncHttpClient;
import com.loopj.android.http.AsyncHttpResponseHandler;
import com.squareup.picasso.Picasso;

import org.apache.http.Header;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;

//import android.support.v7.app.AppCompatActivity;

public class ReturnToMyCar extends ActionBarActivity {
    Context context = this;
    private String TAG  = "Return to My Car";

    static double mLatitude = 0.0;
    static double mLongitude = 0.0;
    static String parkingImgURL = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_return_to_my_car);

        final String request_url = "http://parkingrighthere.appspot.com/park?viewparking=true&recent_one=true&user_email=" + Homepage.email;
        AsyncHttpClient httpClient = new AsyncHttpClient();
        httpClient.get(request_url, new AsyncHttpResponseHandler() {
            @Override
            public void onSuccess(int statusCode, Header[] headers, byte[] response) {

                try {
                    JSONObject jObject = new JSONObject(new String(response));
                    JSONArray parkingLats = jObject.getJSONArray("parkingLat");
                    JSONArray parkingLons = jObject.getJSONArray("parkingLon");
                    JSONArray parkingImgURLs = jObject.getJSONArray("parkingImgURL");

                    if (parkingLats.length() >= 1) {
                        mLatitude = Double.parseDouble(parkingLats.getString(0));
                        mLongitude = Double.parseDouble(parkingLons.getString(0));
                        parkingImgURL = parkingImgURLs.getString(0);
                    }
                } catch (JSONException j) {
                    System.out.println("JSON Error");
                }

            }

            @Override
            public void onFailure(int statusCode, Header[] headers, byte[] errorResponse, Throwable e) {
                Log.e(TAG, "There was a problem in retrieving the url : " + e.toString());
            }
        });

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

    public void viewMap(View view){

    }

    public void routePlanning(View view){

    }

    public void streetView(View view){

    }

    public void shareLocation(View view){

    }

    public void viewPicture(View view){
        if(parkingImgURL != null && !parkingImgURL.isEmpty()) {
            Dialog imageDialog = new Dialog(context);
            imageDialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
            imageDialog.setContentView(R.layout.thumbnail);
            ImageView image = (ImageView) imageDialog.findViewById(R.id.thumbnail_IMAGEVIEW);

            Picasso.with(context).load(parkingImgURL).into(image);

            imageDialog.show();
        }
        else if(parkingImgURL.isEmpty()){
            Toast.makeText(context, "No Picture.", Toast.LENGTH_SHORT).show();
        }
    }

    public void leave(View view){

    }

}
