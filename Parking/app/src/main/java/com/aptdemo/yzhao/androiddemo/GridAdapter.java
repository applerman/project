package com.aptdemo.yzhao.androiddemo;

import android.content.Context;
import android.view.LayoutInflater;
import android.widget.BaseAdapter;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.GridView;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.squareup.picasso.Picasso;

import java.util.ArrayList;

/**
 * Created by chunheng on 10/26/2015.
 */

public class GridAdapter extends BaseAdapter {

    private Context mContext;
    private ArrayList<String> imageURLs;
    private ArrayList<String> texts;
    private LayoutInflater layoutInflater;

    GridAdapter(Context c, ArrayList<String> imageURLs, ArrayList<String> texts){
        mContext = c;
        layoutInflater = LayoutInflater.from(mContext);
        this.imageURLs = imageURLs;
        this.texts = texts;
    }

    public int getCount() {
        return imageURLs.size();
    }

    public Object getItem(int position) {
        return null;
    }

    public long getItemId(int position) {
        return 0;
    }

    public View getView(int position, View convertView, ViewGroup parent) {

        View grid;
        if(convertView==null){
            grid = new View(mContext);
            grid = layoutInflater.inflate(R.layout.gridlayout, null);
        }else{
            grid = (View)convertView;
        }

        ImageView imageView = (ImageView)grid.findViewById(R.id.image);
        imageView.setLayoutParams(new LinearLayout.LayoutParams(200, 200));
        imageView.setScaleType(ImageView.ScaleType.CENTER_CROP);
        Picasso.with(mContext).load(imageURLs.get(position)).into(imageView);
        TextView textView = (TextView)grid.findViewById(R.id.text);
        textView.setText(texts.get(position));

        return grid;
    }

}
