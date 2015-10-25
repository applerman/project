package com.aptdemo.yzhao.androiddemo;

import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.location.Location;
import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.text.style.SubscriptSpan;
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

import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.api.GoogleApiClient;
import com.google.android.gms.location.LocationServices;
import com.loopj.android.http.AsyncHttpClient;
import com.loopj.android.http.AsyncHttpResponseHandler;
import com.squareup.picasso.Picasso;

import org.apache.http.Header;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;

//import android.support.v7.app.AppCompatActivity;

public class DisplayStreams extends ActionBarActivity implements GoogleApiClient.ConnectionCallbacks ,GoogleApiClient.OnConnectionFailedListener {
    Context context = this;
    private String TAG  = "Display Images";

    protected GoogleApiClient mGoogleApiClient;
    protected Location mLastLocation;
    protected double mLatitude;
    protected double mLongitude;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_display_streams);

//        final String request_url = "http://aptandroiddemo.appspot.com/viewAllPhotos";
        final String request_url = "http://connexus0.appspot.com/android?viewstreams=true";
        AsyncHttpClient httpClient = new AsyncHttpClient();
        httpClient.get(request_url, new AsyncHttpResponseHandler() {
            @Override
            public void onSuccess(int statusCode, Header[] headers, byte[] response) {
                final ArrayList<String> imageURLs = new ArrayList<String>();
                final ArrayList<String> imageCaps = new ArrayList<String>();
                try {
                    JSONObject jObject = new JSONObject(new String(response));
                    JSONArray displayImages = jObject.getJSONArray("streamCover");
                    JSONArray displayCaption = jObject.getJSONArray("streamName");

                    for(int i=0;i<displayImages.length();i++) {
                        if(displayImages.getString(i).isEmpty()){
                            imageURLs.add("https://dl.dropboxusercontent.com/u/5338122/images.png");
                        }
                        else {
                            imageURLs.add(displayImages.getString(i));
                        }
                        imageCaps.add(displayCaption.getString(i));
                        System.out.println(displayImages.getString(i));
                    }
                    GridView gridview = (GridView) findViewById(R.id.gridview);
                    gridview.setAdapter(new ImageAdapter(context,imageURLs));
                    gridview.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                        @Override
                        public void onItemClick(AdapterView<?> parent, View v,
                                                int position, long id) {

                            Toast.makeText(context, imageCaps.get(position), Toast.LENGTH_SHORT).show();

                            //Dialog imageDialog = new Dialog(context);
                            //imageDialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
                            //imageDialog.setContentView(R.layout.thumbnail);
                            //ImageView image = (ImageView) imageDialog.findViewById(R.id.thumbnail_IMAGEVIEW);

                            //Picasso.with(context).load(imageURLs.get(position)).into(image);

                            //imageDialog.show();
                            DisplayStreamImages.STREAM = imageCaps.get(position);
                            System.out.println(DisplayStreamImages.STREAM);
                            Intent intent = new Intent(context, DisplayStreamImages.class);
                            startActivity(intent);
                        }
                    });
                }
                catch(JSONException j){
                    System.out.println("JSON Error");
                }

            }

            @Override
            public void onFailure(int statusCode, Header[] headers, byte[] errorResponse, Throwable e) {
                Log.e(TAG, "There was a problem in retrieving the url : " + e.toString());
            }
        });

        Button uploadButton = (Button) findViewById(R.id.view_subscriptions);
        uploadButton.setClickable(true);

        uploadButton.setOnClickListener(
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        Intent intent = new Intent(context, DisplaySubscriptions.class);
                        startActivity(intent);
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

    public void viewNearBy(View view){
        Intent intent= new Intent(this, DisplayNearbyImages.class);
        intent.putExtra("Lat",mLatitude);
        intent.putExtra("Lon",mLongitude);
        startActivity(intent);
    }
    public void viewSearchPage(View view){
        EditText editText = (EditText) findViewById(R.id.edit_message);
        Search.WORD = editText.getText().toString();
        Intent intent= new Intent(this, Search.class);
        startActivity(intent);
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
