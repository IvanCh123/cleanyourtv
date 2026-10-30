package com.gathin.tvhome;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

public class ThemeDirTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();

    private File root() throws IOException {
        return temporary.newFolder("files");
    }

    private File bundle(File root, String name, String config) throws IOException {
        File dir = new File(new File(root, ThemeDir.FOLDER), name);
        assertTrue(dir.mkdirs());
        if (config != null) {
            java.nio.file.Files.write(new File(dir, Config.FILE_NAME).toPath(),
                    config.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
        return dir;
    }

    @Test public void aNameIsOneFolderWithoutDots() {
        assertTrue(ThemeDir.validName("japan"));
        assertTrue(ThemeDir.validName("halloween-2026"));
        assertTrue(ThemeDir.validName("J_1"));
        assertFalse(ThemeDir.validName(""));
        assertFalse(ThemeDir.validName(null));
        assertFalse(ThemeDir.validName(".."));
        assertFalse(ThemeDir.validName("a/b"));
        assertFalse(ThemeDir.validName(".hidden"));
        assertFalse(ThemeDir.validName("japan.theme"));
        assertFalse(ThemeDir.validName("two words"));
        assertFalse(ThemeDir.validName(repeat('a', 41)));
        assertTrue(ThemeDir.validName(repeat('a', 40)));
    }

    @Test public void aBundleIsAFolderWithAReadableConfig() throws IOException {
        File root = root();
        File japan = bundle(root, "japan", "{}");
        assertEquals(japan, ThemeDir.resolve(root, "japan"));
        assertNull(ThemeDir.resolve(root, "nothing"));
        assertNull(ThemeDir.resolve(root, "../japan"));
        assertNull(ThemeDir.resolve(null, "japan"));
    }

    @Test public void anEmptyConfigIsNotABundle() throws IOException {
        File root = root();
        bundle(root, "empty", "");
        assertNull(ThemeDir.resolve(root, "empty"));
        assertEquals(Collections.emptyList(), ThemeDir.bundles(root));
    }

    @Test public void theActiveThemeFallsBackToTheRoot() throws IOException {
        File root = root();
        assertEquals(root, ThemeDir.active(root, ""));
        assertEquals(root, ThemeDir.active(root, "gone"));
        File japan = bundle(root, "japan", "{}");
        assertEquals(japan, ThemeDir.active(root, "japan"));
    }

    @Test public void bundlesAreListedSortedAndOnlyWhenReadable() throws IOException {
        File root = root();
        bundle(root, "zulu", "{}");
        bundle(root, "alpha", "{}");
        bundle(root, "broken", null);
        bundle(root, "empty", "");
        assertEquals(Arrays.asList("alpha", "zulu"), ThemeDir.bundles(root));
        assertEquals(Collections.emptyList(), ThemeDir.bundles(new File(root, "nothing-here")));
        assertEquals(Collections.emptyList(), ThemeDir.bundles(null));
    }

    @Test public void theSignatureCarriesTheBundleName() throws IOException {
        File root = root();
        assertEquals("", ThemeDir.signature(root, ""));
        assertEquals("", ThemeDir.signature(root, "gone"));
        bundle(root, "japan", "{}");
        // Two bundles can hold identical bytes, so the name is what tells a switch apart.
        assertEquals("japan", ThemeDir.signature(root, "japan"));
    }

    private static String repeat(char c, int n) {
        StringBuilder text = new StringBuilder();
        for (int i = 0; i < n; i++) text.append(c);
        return text.toString();
    }
}
