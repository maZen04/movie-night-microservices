| Endpoint | Scenario            | Expected | Result |
| -------- | ------------------- | -------- | ------ |
| Register | Valid data          | 201      | ✅     |
| Register | Duplicate email     | 400      | ✅     |
| Register | Weak password       | 400      | ✅     |
| Login    | Valid credentials   | 200      | ✅     |
| Login    | Wrong password      | 401      | ✅     |
| Refresh  | Invalid refresh     | 401      | ✅     |
| Profile  | No token            | 401      | ✅     |
| Profile  | Valid token         | 200      | ✅     |
| Update   | Change display name | 200      | ✅     |
| Delete   | Valid token         | 204      | ✅     |
| Register | Rate limit exceeded | 429      | ✅     |
