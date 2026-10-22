# Java 25の公式JDKイメージを使用
FROM eclipse-temurin:25-jdk-alpine

WORKDIR /app

# プロジェクトのファイルをすべてコンテナ内にコピー
COPY . .

# gradlewにLinux用の実行権限を付与
RUN chmod +x gradlew

# Gradleでビルドを実行
RUN ./gradlew bootJar --no-daemon

# アプリケーションが使用するポートを指定
EXPOSE 8080

# ▼【修正】配列形式ではなく、シェル形式（または sh -c）に変更する
CMD ["sh", "-c", "java -jar build/libs/*.jar"]