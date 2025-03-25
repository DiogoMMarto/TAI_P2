package pt.ua.tai.database;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;

public class DatabaseReader {
    public static void main(String[] args) throws IOException {
        String s = readTxtFileToString("sequences/db.txt");
        String[] sequences = parseSequencesFromText(s);
        Map<String, String> dbMap = separateNameAndContent(sequences);

        dbMap.entrySet().stream().limit(2).forEach(e -> System.out.println(e.getKey() + " ---> " + e.getValue()));
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

    public static String readTxtFileToString(String fileName) throws IOException {
        return Files.readString(Paths.get(fileName));
    }
}
