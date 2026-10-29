#include <iostream>
#include <vector>
using namespace std;

int main() {
    vector<string> staff = {"Ravi", "Meena", "Arun"};
    vector<string> tasks = {"Classroom Cleaning", "Lab Sanitization", "Ground Cleaning"};
    for (int i = 0; i < staff.size(); i++) {
        cout << staff[i] << " -> " << tasks[i % tasks.size()] << endl;
    }
    return 0;
}
