using System.Numerics;
using System.Security.Cryptography;

public class IDGenerator {
    private const string digits = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

    public static string Generate(int length)
    {
        var data = RandomNumberGenerator.GetBytes(length);

        // Decode byte[] to BigInteger
        BigInteger intData = 0;
        for (int i = 0; i < data.Length; i++)
        {
            intData = intData * 256 + data[i];
        }

        // Encode BigInteger to Base58 string
        var result = string.Empty;
        while (intData > 0)
        {
            var remainder = (int)(intData % 58);
            intData /= 58;
            result = digits[remainder] + result;
        }

        // Append `1` for each leading 0 byte
        for (int i = 0; i < data.Length && data[i] == 0; i++)
        {
            result = '1' + result;
        }

        return result;
    }
}