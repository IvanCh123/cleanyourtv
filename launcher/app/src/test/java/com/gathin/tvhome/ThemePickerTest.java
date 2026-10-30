package com.gathin.tvhome;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class ThemePickerTest {

    @Test
    public void bundleNamesReadAsMenuLabels() {
        assertEquals("Japan", ThemePicker.label("japan"));
        assertEquals("Christmas", ThemePicker.label("christmas"));
        assertEquals("New year 2027", ThemePicker.label("new-year_2027"));
        assertEquals("Retro", ThemePicker.label("Retro"));
    }

    @Test
    public void aNameOfSeparatorsAloneStaysAsItIs() {
        assertEquals("--", ThemePicker.label("--"));
    }
}
