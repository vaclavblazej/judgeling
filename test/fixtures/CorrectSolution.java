import java.util.Arrays;
import java.util.Scanner;

public class CorrectSolution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        long[] a = new long[n];
        for (int i = 0; i < n; i++) a[i] = sc.nextLong();
        Arrays.sort(a);
        StringBuilder sb = new StringBuilder();
        for (long x : a) sb.append(x).append(' ');
        System.out.println(sb.toString());
    }
}
