/*
 * Copyright (C) 2012 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.aptdemo.yzhao.androiddemo;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.widget.CheckBox;
import android.widget.Toast;

import com.google.android.gms.maps.OnStreetViewPanoramaReadyCallback;
import com.google.android.gms.maps.StreetViewPanorama;
import com.google.android.gms.maps.SupportStreetViewPanoramaFragment;
import com.google.android.gms.maps.model.LatLng;
import com.google.android.gms.maps.model.StreetViewPanoramaLocation;

/**
 * This shows how to create an activity with static streetview (all options have been switched off)
 */
public class StreetView extends AppCompatActivity {

    // Cole St, San Fran
//    private static final LatLng SAN_FRAN = new LatLng(37.765927, -122.449972);

    private static LatLng location;

    private StreetViewPanorama mStreetViewPanorama;

    private CheckBox mStreetNameCheckbox;

    private CheckBox mNavigationCheckbox;

    private CheckBox mZoomCheckbox;

    private CheckBox mPanningCheckbox;

    Context context = this;

    @Override
    protected void onCreate(final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_street_view);

        Intent intent = getIntent();
        double lat = intent.getDoubleExtra("Lat", 0.0);
        double lon = intent.getDoubleExtra("Lon", 0.0);
        location = new LatLng(lat, lon);

        mStreetNameCheckbox = (CheckBox) findViewById(R.id.streetnames);
        mNavigationCheckbox = (CheckBox) findViewById(R.id.navigation);

        SupportStreetViewPanoramaFragment streetViewPanoramaFragment =
                (SupportStreetViewPanoramaFragment)
                        getSupportFragmentManager().findFragmentById(R.id.streetviewpanorama);
        streetViewPanoramaFragment.getStreetViewPanoramaAsync(
                new OnStreetViewPanoramaReadyCallback() {
                    @Override
                    public void onStreetViewPanoramaReady(StreetViewPanorama panorama) {
                        mStreetViewPanorama = panorama;
                        mStreetViewPanorama.setStreetNamesEnabled(mStreetNameCheckbox.isChecked());
                        mStreetViewPanorama
                                .setUserNavigationEnabled(mNavigationCheckbox.isChecked());
                        mStreetViewPanorama.setZoomGesturesEnabled(true);
                        mStreetViewPanorama.setPanningGesturesEnabled(true);

                        // Only set the panorama to SAN_FRAN on startup (when no panoramas have been
                        // loaded which is when the savedInstanceState is null).
                        if (savedInstanceState == null) {
                            mStreetViewPanorama.setPosition(location);
                        }
                    }
                });
    }

    private boolean checkReady() {
        if (mStreetViewPanorama == null) {
            Toast.makeText(this, R.string.map_not_ready, Toast.LENGTH_SHORT).show();
            return false;
        }
        return true;
    }

    public void onStreetNamesToggled(View view) {
        if (!checkReady()) {
            return;
        }
        mStreetViewPanorama.setStreetNamesEnabled(mStreetNameCheckbox.isChecked());
    }

    public void onNavigationToggled(View view) {
        if (!checkReady()) {
            return;
        }
        mStreetViewPanorama.setUserNavigationEnabled(mNavigationCheckbox.isChecked());
    }
}
