package com.gathin.tvhome;

import java.util.List;
import java.util.regex.Pattern;

/** The files ThemeProvider may write or delete under Config.dir, by the URI's path segments. */
final class ThemeFiles {
    static final String WALLPAPERS = "wallpapers";
    /** The names tools/theme.sh accepts for a collection image, and the types WallpaperRotation reads. */
    private static final Pattern IMAGE = Pattern.compile("[A-Za-z0-9_.-]+\\.(jpg|jpeg|png|webp)",
            Pattern.CASE_INSENSITIVE);

    private ThemeFiles() {}

    /**
     * The path relative to the theme directory, e.g. "config.json", "wallpapers/dusk.jpg" or
     * "themes/japan/config.json", or null if refused. The root files are what tools/theme.sh has always
     * written; a bundle is the same set of files one folder down.
     */
    static String path(List<String> segments) {
        if (segments == null || segments.isEmpty()) return null;
        if (ThemeDir.FOLDER.equals(segments.get(0))) {
            // themes/<name> itself is only a delete (isBundle), never a file to open.
            if (segments.size() < 2 || !ThemeDir.validName(segments.get(1))) return null;
            String inner = plain(segments.subList(2, segments.size()));
            return inner == null ? null : ThemeDir.FOLDER + "/" + segments.get(1) + "/" + inner;
        }
        return plain(segments);
    }

    /** The files at the root of the theme folder. */
    private static String plain(List<String> segments) {
        if (segments == null || segments.isEmpty()) return null;
        if (segments.size() == 1) {
            String name = segments.get(0);
            return Config.FILE_NAME.equals(name) || "wallpaper.jpg".equals(name) || "theme_revision".equals(name)
                    ? name : null;
        }
        if (segments.size() == 2 && WALLPAPERS.equals(segments.get(0))
                && (collectionImage(segments.get(1)) || WallpaperCaptions.FILE_NAME.equals(segments.get(1)))) {
            return WALLPAPERS + "/" + segments.get(1);
        }
        return null;
    }

    /** True for "wallpapers" alone: a delete of it clears the collection's images. */
    static boolean isCollection(List<String> segments) {
        return segments != null && segments.size() == 1 && WALLPAPERS.equals(segments.get(0));
    }

    /** True for "themes/<name>" alone: a delete of it removes that bundle from the TV. */
    static boolean isBundle(List<String> segments) {
        return segments != null && segments.size() == 2 && ThemeDir.FOLDER.equals(segments.get(0))
                && ThemeDir.validName(segments.get(1));
    }

    static boolean collectionImage(String name) {
        return name != null && !name.startsWith(".") && IMAGE.matcher(name).matches();
    }
}
