package pt.ua.tai.database;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
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
            StringBuilder content = new StringBuilder();
            Arrays.stream(parts).skip(1).forEach(content::append);
            String filteredContent = content.toString().replaceAll("[^ATCG]", "");
            dbMap.put(parts[0], filteredContent);
        });
        return dbMap;
    }

    private static String[] parseSequencesFromText(String s) {
        return Arrays.stream(s.split("@")).skip(1).toArray(String[]::new);
    }

    public static String readTxtFileToString(String filePath) throws IOException {
        return Files.readString(Paths.get(filePath));
    }
    public static void writeListToFile(String filePath, List<Double> list){
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(filePath))) {
            for (Double number : list) {
                writer.write(number.toString()); // Convert double to String
                writer.newLine(); // Move to the next line
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
