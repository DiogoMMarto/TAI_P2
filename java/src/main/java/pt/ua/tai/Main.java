package pt.ua.tai;

import picocli.CommandLine;
import picocli.CommandLine.Option;
import pt.ua.tai.meta.Meta;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;

import static pt.ua.tai.database.DatabaseReader.*;

public class Main implements Callable<Integer> {
    @Option(names = {"-fm", "--file-meta"}, description = "File path for meta", defaultValue = "sequences/meta.txt", required = true)
    private String fileNameMeta;
    @Option(names = {"-fd", "--file-db"}, description = "File path for db/sequences", defaultValue = "sequences/db.txt", required = true)
    private String fileNameDb;
    @Option(names = {"-v", "--verbose"}, description = "Verbose output", defaultValue = "false")
    private boolean verbose;
    @Option(names = {"-a", "--alpha"}, description = "Smoothing parameter alpha", defaultValue = "1")
    private Float alpha;
    @Option(names = {"-k", "--contextWidth"}, description = "Context width", defaultValue = "13")
    private Integer k;
    @Option(names = {"-t", "--top"}, description = "Top t results", defaultValue = "20")
    private Integer t;
    @Option(names = {"-p", "--nrcProgression"}, description = "Progression of nrc during the sequence, indicate the output folder")
    private String progressionFolder;

    public static void main(String[] args) {
        System.setProperty("java.util.logging.SimpleFormatter.format", "Time: %1$tT.%1$tL -> %4$s %5$s%6$s%n");
        int exitCode = new CommandLine(new Main()).execute(args);
        System.exit(exitCode);
    }

    @Override
    public Integer call() {
        try {
            Map<String, String> dbMap = readFileAndCreateDbMap(fileNameDb);
            String metaContent = readTxtFileToString(fileNameMeta);
            Meta meta = new Meta(metaContent, k);
            Map<String, Double> best = meta.getBestSequences(dbMap, alpha, t);
            if(progressionFolder!=null){
                for (Map.Entry<String, Double> entry : best.entrySet()) {
                    List<Double> progression=meta.getNRCProgression(dbMap.get(entry.getKey()),alpha);
                    // Replace invalid characters with underscores
                    String fileName = entry.getKey()
                            .replaceAll("[\\\\/:*?\"<>|]", "_")  // Replace invalid characters
                            .trim(); // Remove trailing/leading spaces

                    if (fileName.length() > 50) {
                        fileName = fileName.substring(0, 50);
                    }
                    progressionFolder=progressionFolder.replaceAll("\\.","_");
                    Path folderPath = Paths.get(progressionFolder);
                    if (!Files.exists(folderPath)) {
                        try {
                            Files.createDirectories(folderPath);
                        } catch (IOException e) {
                            throw new RuntimeException(e);
                        }
                    }
                    String filePath = Paths.get(progressionFolder, fileName+".txt").toString();
                    System.out.println("Writing to file: '" + filePath + "'");
                    writeListToFile(filePath,progression);
                }
            }

            best.entrySet().stream()
                    .sorted(Map.Entry.comparingByValue())
                    .forEach(e -> System.out.println(e.getValue() + "\t" + e.getKey()));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        return 1;
    }
}