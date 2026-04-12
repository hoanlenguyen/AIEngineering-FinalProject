// Test sample for CodeSentinel — intentional bugs, style issues, and security vulnerabilities

using System;
using System.Data.SqlClient;

public class TestSample
{
    // Security: hardcoded credentials in connection string (HIGH)
    private string connectionString = "Server=localhost;Password=admin123";

    // Security: SQL injection via string concatenation (HIGH)
    public string GetUser(string userId)
    {
        string query = "SELECT * FROM Users WHERE Id = " + userId;
        using (SqlConnection conn = new SqlConnection(connectionString))
        {
            SqlCommand cmd = new SqlCommand(query, conn);
            conn.Open();
            return cmd.ExecuteScalar()?.ToString();
        }
    }

    // Bug: no guard against division by zero — throws DivideByZeroException
    public int Divide(int a, int b)
    {
        return a / b;
    }

    // Bug: off-by-one — i <= items.Length causes IndexOutOfRangeException
    public void ProcessItems(string[] items)
    {
        for (int i = 0; i <= items.Length; i++)
        {
            Console.WriteLine(items[i]);
        }
    }

    // Style: method name should be PascalCase (BadMethod)
    // Style: missing spaces around operators and after 'if'
    public void badMethod()
    {
        var x=1;
        var unused="never used";  // Style: unused variable
        if(x==1)
            Console.WriteLine("bad style");
    }
}
