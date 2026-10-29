#include <stdio.h>

int main() {
    int staff, present;
    printf("Enter total staff: ");
    scanf("%d", &staff);
    printf("Enter number present: ");
    scanf("%d", &present);
    printf("Attendance: %d/%d present (%.2f%%)\n", present, staff, (present*100.0)/staff);
    return 0;
}
