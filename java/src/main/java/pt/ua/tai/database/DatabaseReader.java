package pt.ua.tai.database;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;

public class DatabaseReader {
    private DatabaseReader() {
    }

    public static Map<String, String> readFileAndCreateDbMap(String filePath) throws IOException {
        String s = readTxtFileToString(filePath);
        String[] sequences = parseSequencesFromText(s);
        return separateNameAndContent(sequences);
    }

    private static Map<String, String> separateNameAndContent(String[] sequences) {
        Map<String, String> dbMap = new LinkedHashMap<>();
        Arrays.stream(sequences).forEach(it -> {
            final String[] parts = it.split("\n");
            dbMap.put(parts[0], parts[1]);
        });
        return dbMap;
    }

    private static String[] parseSequencesFromText(String s) {
        return Arrays.stream(s.split("@")).skip(1).toArray(String[]::new);
    }

    public static String readTxtFileToString(String filePath) throws IOException {
        return Files.readString(Paths.get(filePath));
    }
}
