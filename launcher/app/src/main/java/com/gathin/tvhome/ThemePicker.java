package com.gathin.tvhome;

import android.content.Context;
import android.content.SharedPreferences;

import java.io.File;
import java.util.Locale;

/**
 * What the Themes menu (Home's long-press Settings menu, then Themes) lists and saves: the root theme
 * ("Default", what tools/theme.sh has always pushed) or one of the bundles under files/themes/. MainActivity
 * draws the list as the same glass menu as the Settings one. The choice goes into Launcher settings and Home
 * rebuilds, the same path every other setting takes; Config.load() drops the columns, dock opacity and wallpaper
 * picked on the TV when the theme's signature changes.
 */
final class ThemePicker {
    private ThemePicker() {}

    /** The theme Home is showing: "" for Default; a stale name already fell back to the root theme in Config.load(). */
    static String current(Context ctx, File root) {
        String saved = prefs(ctx).getString(ThemeDir.KEY, "");
        return ThemeDir.resolve(root, saved) != null ? saved : "";
    }

    /** Saves {@code pick} ("" for Default); false when it is the theme already showing, so nothing needs rebuilding. */
    static boolean choose(Context ctx, File root, String pick) {
        if (pick.equals(current(ctx, root))) return false;
        prefs(ctx).edit().putString(ThemeDir.KEY, pick).apply();
        return true;
    }

    /** A bundle's folder name as a menu label: "new-year_2027" reads "New year 2027". */
    static String label(String bundle) {
        String words = bundle.replace('-', ' ').replace('_', ' ').trim();
        if (words.isEmpty()) return bundle;
        return words.substring(0, 1).toUpperCase(Locale.ROOT) + words.substring(1);
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(Config.SETTINGS_NAME, Context.MODE_PRIVATE);
    }
}
