package com.gathin.tvhome;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Theme bundles kept beside the pushed theme. The root of the theme folder
 * ({@code /sdcard/Android/data/com.gathin.tvhome/files/}) is what tools/theme.sh has always written, and
 * stays the theme in use until Launcher settings names a bundle: {@code themes/<name>/} holds one more
 * config.json and its wallpaper, the same four files as the root. A name that is gone or broken falls back
 * to the root theme, so Home never comes up with no config at all.
 */
final class ThemeDir {
    /** Launcher settings key: the bundle to use, empty for the root theme. */
    static final String KEY = "theme_choice";
    /** The folder under Config.dir() that holds the bundles. */
    static final String FOLDER = "themes";
    /** A bundle folder name: letters, digits, underscore and hyphen. No dots, so no ".." and no hidden names. */
    private static final Pattern NAME = Pattern.compile("[A-Za-z0-9_-]{1,40}");

    private ThemeDir() {}

    static boolean validName(String name) {
        return name != null && NAME.matcher(name).matches();
    }

    /** {@code themes/<name>} under root, or null when the name is refused or the bundle has no readable config.json. */
    static File resolve(File root, String name) {
        if (root == null || !validName(name)) return null;
        File dir = new File(new File(root, FOLDER), name);
        File config = new File(dir, Config.FILE_NAME);
        return config.isFile() && config.length() > 0 ? dir : null;
    }

    /** The bundle the saved choice names, or the root theme when there is no choice, it is gone, or it is broken. */
    static File active(File root, String name) {
        File picked = resolve(root, name);
        return picked != null ? picked : root;
    }

    /** The bundles that can be shown, sorted by name. A folder without a readable config.json is not a bundle. */
    static List<String> bundles(File root) {
        List<String> names = new ArrayList<>();
        File[] entries = root == null ? null : new File(root, FOLDER).listFiles();
        if (entries == null) return names;
        for (File entry : entries) {
            String name = entry.getName();
            if (entry.isDirectory() && resolve(root, name) != null) names.add(name);
        }
        Collections.sort(names);
        return names;
    }

    /**
     * The active theme's name for the on-TV choice signature: "" for the root theme, the bundle's name
     * otherwise. Two bundles can hold identical bytes, so the name has to be part of it; without that a
     * switch would not clear the columns, dock opacity or wallpaper picked on the TV for the old theme.
     */
    static String signature(File root, String name) {
        return resolve(root, name) != null ? name : "";
    }
}
