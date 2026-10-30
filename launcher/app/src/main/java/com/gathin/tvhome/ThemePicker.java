package com.gathin.tvhome;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;

import java.io.File;
import java.util.List;

/**
 * The Themes row in Home's long-press Settings menu: picks which stored theme Home shows, the root theme
 * ("Default", what tools/theme.sh has always pushed) or one of the bundles under files/themes/. The choice
 * goes into Launcher settings and Home rebuilds, the same path every other setting takes; Config.load() drops
 * the columns, dock opacity and wallpaper picked on the TV when the theme's signature changes.
 */
final class ThemePicker {
    private ThemePicker() {}

    /** Shows the list; {@code onChanged} runs after a different theme was saved. */
    static void show(Activity activity, Runnable onChanged) {
        File root = Config.dir(activity);
        List<String> bundles = ThemeDir.bundles(root);
        SharedPreferences choices = activity.getSharedPreferences(Config.SETTINGS_NAME, Activity.MODE_PRIVATE);
        String saved = choices.getString(ThemeDir.KEY, "");
        // What Home is showing now: a stale name already fell back to the root theme in Config.load().
        String current = ThemeDir.resolve(root, saved) != null ? saved : "";
        String[] labels = new String[bundles.size() + 1];
        labels[0] = activity.getString(R.string.themes_default);
        int checked = 0;
        for (int i = 0; i < bundles.size(); i++) {
            labels[i + 1] = bundles.get(i);
            if (bundles.get(i).equals(current)) checked = i + 1;
        }
        new AlertDialog.Builder(activity)
                .setTitle(R.string.themes_label)
                .setSingleChoiceItems(labels, checked, (dialog, which) -> {
                    dialog.dismiss();
                    String pick = which == 0 ? "" : bundles.get(which - 1);
                    if (pick.equals(current)) return;
                    choices.edit().putString(ThemeDir.KEY, pick).apply();
                    onChanged.run();
                })
                .setNegativeButton(android.R.string.cancel, null)
                .show();
    }
}
