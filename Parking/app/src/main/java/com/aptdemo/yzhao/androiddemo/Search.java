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
import android.widget.EditText;
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

public class Search extends ActionBarActivity {
    Context context = this;
    private String TAG  = "Display Images";
    private String SearchedWord = "";
    public static String WORD = "";
    public static int lastInd = 0;
    private int curIdx = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_display_search);

        curIdx = Search.lastInd;
        Search.lastInd = 0;
//        final String request_url = "http://aptandroiddemo.appspot.com/viewAllPhotos";
        //final String request_url = "http://phase3back.appspot.com/viewAllPhotos";
        SearchedWord = Search.WORD;
        final String request_url = "http://connexus0.appspot.com/android?search=true&show=" + SearchedWord;
        Search.WORD = "";

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
                    JSONArray count = jObject.getJSONArray("count");

                    if(!SearchedWord.isEmpty()) {
                        TextView tv = (TextView) findViewById(R.id.search_result);
                        tv.setText(count.getString(0) + " results for " + SearchedWord + "\nClick on an image to view stream.");
                    }

                    int max_images = Math.min(displayImages.length() - curIdx, 8);

                    for (int i = curIdx; i < curIdx + max_images; i++) {
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
                    gridview.setAdapter(new GridAdapter(context,imageURLs,imageCaps));
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

                    if(displayImages.length() - curIdx > 8) {
                        Button uploadButton = (Button) findViewById(R.id.more_images);
                        uploadButton.setClickable(true);

                        uploadButton.setOnClickListener(
                                new View.OnClickListener() {
                                    @Override
                                    public void onClick(View v) {
                                        finish();
                                        Search.lastInd = curIdx + 8;
                                        Search.WORD = SearchedWord;
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
    public void viewSearchPage(View view){
        EditText editText = (EditText) findViewById(R.id.edit_message);
        Search.WORD = editText.getText().toString();
        Intent intent= new Intent(this, Search.class);
        startActivity(intent);
    }
}
