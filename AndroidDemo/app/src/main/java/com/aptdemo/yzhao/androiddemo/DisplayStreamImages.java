package com.aptdemo.yzhao.androiddemo;

import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.Window;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.TextView;
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

public class DisplayStreamImages extends ActionBarActivity {
    public static String STREAM = "";
    public static int lastInd = 0;
    Context context = this;
    private String TAG  = "Display Images";
    private String curStream = "";
    private int curIdx = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_display_streamimages);

        curStream = DisplayStreamImages.STREAM;
        curIdx = DisplayStreamImages.lastInd;
        DisplayStreamImages.lastInd = 0;

        TextView tv = (TextView) findViewById(R.id.view_a_stream);
        tv.setText("View A Stream: " + curStream);




//        final String request_url = "http://aptandroiddemo.appspot.com/viewAllPhotos";
        final String request_url = "http://connexus0.appspot.com/android?viewpictures=true&stream=" + curStream;
        AsyncHttpClient httpClient = new AsyncHttpClient();
        httpClient.get(request_url, new AsyncHttpResponseHandler() {
            @Override
            public void onSuccess(int statusCode, Header[] headers, byte[] response) {
                final ArrayList<String> imageURLs = new ArrayList<String>();
                final ArrayList<String> imageCaps = new ArrayList<String>();
                try {
                    JSONObject jObject = new JSONObject(new String(response));
                    JSONArray displayImages = jObject.getJSONArray("pictureURL");
                    JSONArray displayCaption = jObject.getJSONArray("pictureCaption");

                    int max_images = Math.min(displayImages.length() - curIdx, 16);




                    for (int i = curIdx; i < curIdx + max_images; i++) {

                        imageURLs.add(displayImages.getString(i));
                        imageCaps.add(displayCaption.getString(i));
                        System.out.println(displayImages.getString(i));
                    }
                    GridView gridview = (GridView) findViewById(R.id.gridview);
                    //gridview.setAdapter(new ImageAdapter(context, imageURLs));
                    gridview.setAdapter(new GridAdapter(context, imageURLs, imageCaps));
                    gridview.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                        @Override
                        public void onItemClick(AdapterView<?> parent, View v,
                                                int position, long id) {

                            Toast.makeText(context, imageCaps.get(position), Toast.LENGTH_SHORT).show();

                            Dialog imageDialog = new Dialog(context);
                            imageDialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
                            imageDialog.setContentView(R.layout.thumbnail);
                            ImageView image = (ImageView) imageDialog.findViewById(R.id.thumbnail_IMAGEVIEW);

                            Picasso.with(context).load(imageURLs.get(position)).into(image);

                            imageDialog.show();
                        }
                    });

                    if(displayImages.length() - curIdx > 16) {
                        Button uploadButton = (Button) findViewById(R.id.more_images);
                        uploadButton.setClickable(true);

                        uploadButton.setOnClickListener(
                                new View.OnClickListener() {
                                    @Override
                                    public void onClick(View v) {
                                        finish();
                                        DisplayStreamImages.lastInd = curIdx + 16;
                                        startActivity(getIntent());
                                    }
                                }
                        );
                    }
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

    /*
    public void viewAllStreams(View view){
        Intent intent= new Intent(this, DisplayStreams.class);
        startActivity(intent);
    }
*/
    public void uploadImages(View view) {
        DisplayStreamImages.STREAM = curStream;
        Intent intent = new Intent(context, ImageUpload.class);
        startActivity(intent);
    }

}
