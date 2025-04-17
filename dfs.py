def isvalid(matrix, x, y) -> bool:
    if matrix is None:
        print("none map")
        exit(1)
    if x < 0 or y < 0 or x >= len(matrix) or y >= len(matrix[0]):
        return False
    return matrix[x][y] == 0

def dfs(matrix, start_x, start_y, end_x, end_y) -> list:
    visited = set()
    path = []
    
    def dfs_helper(x, y):
        if x == end_x and y == end_y:
            path.append([x, y])
            return True

        if not isvalid(matrix, x, y) or (x, y) in visited:
            return False
        visited.add((x, y))
        path.append([x, y])
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        for dx, dy in directions:
            if dfs_helper(x + dx, y + dy):
                return True

        path.pop()
        return False

    dfs_helper(start_x, start_y)
    return path

# 测试代码
if __name__ == "__main__":
    # 示例地图：0表示通道，1表示障碍物
    test_map = [
        [0, 0, 1, 0, 0],
        [0, 1, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [1, 1, 0, 0, 0],
        [0, 0, 0, 1, 0]
    ]
    
    # 寻找从(0,0)到(4,4)的路径
    result = dfs(test_map, 0, 0, 4, 4)
    
    if result:
        print("找到路径:")
        for point in result:
            print(f"({point[0]}, {point[1]})")
    else:
        print("没有找到路径")