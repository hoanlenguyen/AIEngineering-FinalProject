// Test sample for CodeSentinel — intentional bugs, style issues, and security vulnerabilities

import java.sql.*;
import java.io.*;

public class TestSample {

    // Security: hardcoded password (HIGH)
    private static String DB_PASSWORD = "hardcoded_password_123";

    // Security: SQL injection via string concatenation (HIGH)
    public static String getUserById(Connection conn, String userId) throws SQLException {
        String query = "SELECT * FROM users WHERE id = " + userId;
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(query);
        if (rs.next()) {
            return rs.getString("username");
        }
        return null;
    }

    // Bug: resource leak — FileWriter never closed
    // Bug: silent catch — exception swallowed
    public static void writeToFile(String filename, String content) {
        try {
            FileWriter fw = new FileWriter(filename);
            fw.write(content);
        } catch (IOException e) {
            // exception silently ignored
        }
    }

    // Bug: no guard against division by zero
    public static int divide(int a, int b) {
        return a / b;
    }

    // Style: missing Javadoc; method name should be camelCase (processData)
    public static void ProcessData(String[] items) {
        for (int i=0; i<items.length; i++) {  // Style: missing spaces around =
            System.out.println(items[i]);
        }
    }

    public static void main(String[] args) {
        int result = divide(10, 0);  // Bug: throws ArithmeticException at runtime
        System.out.println(result);
    }
}
